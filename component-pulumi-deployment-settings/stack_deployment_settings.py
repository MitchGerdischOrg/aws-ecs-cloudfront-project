"""StackDeploymentSettings: configures Pulumi Deployments for a stack via the Pulumi Cloud (pulumiservice) provider.

Repository, branch, repo dir and trigger paths default to values read from the local git checkout
of the calling program. The component provider process runs in the program's directory, so git
commands and Pulumi.yaml reads here see the program's repo, not this package's.
"""

import os
import posixpath
import subprocess
from typing import TypedDict

import pulumi
import pulumi_pulumiservice as pulumiservice
import yaml

_DEFAULT_VCS_PROVIDER = "github"
_DEFAULT_BRANCH = "main"
_DEFAULT_OIDC_SESSION_NAME = "pulumi-deployments"


def _git(*git_args: str) -> str | None:
    """Runs a git command in the program directory; returns None if git or the repo is unavailable."""
    try:
        result = subprocess.run(
            ["git", *git_args], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _detect_repository() -> str | None:
    """Converts the 'origin' remote URL (https, ssh, or scp-style) to 'owner/repo'."""
    url = _git("remote", "get-url", "origin")
    if not url:
        return None
    parts = url.removesuffix(".git").replace(":", "/").rstrip("/").split("/")
    return "/".join(parts[-2:]) if len(parts) >= 2 else None


def _detect_branch() -> str | None:
    """The checked-out branch, else the remote's default branch (e.g. on a detached HEAD)."""
    branch = _git("rev-parse", "--abbrev-ref", "HEAD")
    if branch and branch != "HEAD":
        return branch
    remote_head = _git("symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return remote_head.removeprefix("origin/") if remote_head else None


def _detect_repo_dir() -> str:
    """The program directory's path relative to the repo root ('' at the root)."""
    return (_git("rev-parse", "--show-prefix") or "").strip("/")


def _detect_trigger_paths(repo_dir: str) -> list[str]:
    """The program folder plus any local-path packages in Pulumi.yaml that live in the same repo."""
    paths = [f"{repo_dir}/**" if repo_dir else "**"]
    try:
        with open("Pulumi.yaml") as f:
            packages = (yaml.safe_load(f) or {}).get("packages") or {}
    except (OSError, yaml.YAMLError):
        return paths
    for source in packages.values():
        # Packages are either a plain source string or a mapping with a 'source' key.
        if isinstance(source, dict):
            source = source.get("source")
        if not isinstance(source, str) or not source.startswith("."):
            continue
        package_dir = posixpath.normpath(posixpath.join(repo_dir, source))
        if not package_dir.startswith(".."):
            paths.append(f"{package_dir}/**")
    return paths


class StackDeploymentSettingsArgs(TypedDict):
    repository: pulumi.Input[str] | None
    """The repository to deploy from, e.g. 'my-org/my-repo' for GitHub. Defaults to the local git 'origin' remote."""

    organization: pulumi.Input[str] | None
    """The Pulumi organization that owns the stack. Defaults to the organization of the stack running this program."""

    project: pulumi.Input[str] | None
    """The Pulumi project of the stack. Defaults to the project running this program."""

    stack: pulumi.Input[str] | None
    """The name of the stack to configure. Defaults to the stack running this program."""

    vcs_provider: pulumi.Input[str] | None
    """The VCS integration to use: 'github' (default), 'gitlab', 'bitbucket', 'azure_devops' or 'custom'. The integration must already be set up in the Pulumi org."""

    branch: pulumi.Input[str] | None
    """The branch to deploy. Defaults to the locally checked-out branch, else 'main'."""

    repo_dir: pulumi.Input[str] | None
    """The folder within the repository that contains the project's Pulumi.yaml. Defaults to the program's folder in the local git checkout."""

    deploy_commits: pulumi.Input[bool] | None
    """Run `pulumi up` when commits are pushed to the branch. Defaults to true."""

    preview_pull_requests: pulumi.Input[bool] | None
    """Run `pulumi preview` when a pull request is opened against the branch. Defaults to true."""

    paths: pulumi.Input[list[pulumi.Input[str]]] | None
    """Only trigger deployments for changes under these repository paths (glob patterns). Defaults to the repo dir plus any local-path packages in Pulumi.yaml."""

    agent_pool_id: pulumi.Input[str] | None
    """The ID of a customer-managed agent (runner) pool. Defaults to Pulumi-hosted runners."""

    executor_image: pulumi.Input[str] | None
    """A custom executor image, e.g. 'pulumi/pulumi-python:latest'. Defaults to the Pulumi-provided image."""

    environment_variables: pulumi.Input[dict[str, pulumi.Input[str]]] | None
    """Environment variables to set for the deployment. Wrap sensitive values with pulumi.Output.secret()."""

    pre_run_commands: pulumi.Input[list[pulumi.Input[str]]] | None
    """Shell commands to run before the Pulumi operation executes."""

    aws_oidc_role_arn: pulumi.Input[str] | None
    """The ARN of an AWS IAM role to assume via OIDC during the deployment. OIDC is only configured when this is set."""

    aws_oidc_session_name: pulumi.Input[str] | None
    """The name of the AWS assume-role session. Defaults to 'pulumi-deployments'."""

    aws_oidc_duration: pulumi.Input[str] | None
    """The duration of the AWS assume-role session in 'XhYmZs' format, e.g. '1h0m0s'."""


class StackDeploymentSettings(pulumi.ComponentResource):
    stack_name: pulumi.Output[str]
    """The fully qualified name ('org/project/stack') of the stack the settings apply to."""

    def __init__(
        self,
        name: str,
        args: StackDeploymentSettingsArgs,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__(
            "deployment-settings:index:StackDeploymentSettings", name, {}, opts
        )

        child_opts = pulumi.ResourceOptions(parent=self)

        def arg(key: str, default=None):
            value = args.get(key)
            return default if value is None else value

        organization = arg("organization", pulumi.get_organization())
        project = arg("project", pulumi.get_project())
        stack = arg("stack", pulumi.get_stack())

        # Fill anything not provided from the local git checkout of the calling program.
        repository = arg("repository") or _detect_repository()
        if not repository:
            raise ValueError(
                f"{name}: could not determine the repository from git in {os.getcwd()}; "
                "set the 'repository' input."
            )
        branch = arg("branch") or _detect_branch() or _DEFAULT_BRANCH
        repo_dir = arg("repo_dir", _detect_repo_dir())
        paths = arg("paths") or pulumi.Output.from_input(repo_dir).apply(
            _detect_trigger_paths
        )

        # Only configure OIDC when a role is provided.
        oidc = None
        role_arn = args.get("aws_oidc_role_arn")
        if role_arn is not None:
            oidc = pulumiservice.OperationContextOIDCArgs(
                aws=pulumiservice.AWSOIDCConfigurationArgs(
                    role_arn=role_arn,
                    session_name=arg("aws_oidc_session_name", _DEFAULT_OIDC_SESSION_NAME),
                    duration=args.get("aws_oidc_duration"),
                )
            )

        executor_context = None
        executor_image = args.get("executor_image")
        if executor_image is not None:
            executor_context = pulumiservice.DeploymentSettingsExecutorContextArgs(
                executor_image=executor_image,
            )

        settings = pulumiservice.DeploymentSettings(
            f"{name}-deployment-settings",
            organization=organization,
            project=project,
            stack=stack,
            # Leaving the agent pool unset runs deployments on Pulumi Cloud hosted runners.
            agent_pool_id=args.get("agent_pool_id"),
            executor_context=executor_context,
            vcs=pulumiservice.DeploymentSettingsVcsArgs(
                provider=arg("vcs_provider", _DEFAULT_VCS_PROVIDER),
                repository=repository,
                deploy_commits=arg("deploy_commits", True),
                preview_pull_requests=arg("preview_pull_requests", True),
                paths=paths,
            ),
            # With a VCS integration, the repo URL and auth come from the integration;
            # only the branch and project folder are needed here.
            source_context=pulumiservice.DeploymentSettingsSourceContextArgs(
                git=pulumiservice.DeploymentSettingsGitSourceArgs(
                    branch=branch,
                    # An empty repo dir means the repo root, which is the service default.
                    repo_dir=pulumi.Output.from_input(repo_dir).apply(
                        lambda d: d or None
                    ),
                )
            ),
            operation_context=pulumiservice.DeploymentSettingsOperationContextArgs(
                environment_variables=args.get("environment_variables"),
                pre_run_commands=args.get("pre_run_commands"),
                oidc=oidc,
            ),
            opts=child_opts,
        )

        self.stack_name = pulumi.Output.concat(
            settings.organization, "/", settings.project, "/", settings.stack
        )

        self.register_outputs({"stack_name": self.stack_name})
