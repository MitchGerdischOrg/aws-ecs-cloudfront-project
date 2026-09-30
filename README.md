# aws-ecs-cloudfront-project
Pulumi project that deploys to ECS with a Cloudfront CDN and uses a component resource.

# Set Up Steps

- Create an empty repo and clone it.
- In the repo folder, run `pulumi new https://github.com/MitchGerdischOrg/aws-ecs-cloudfront-project/tree/main/aws-ecs-cloudfront-py`
  - You are prompted for the project name, description, stack name, and `agentPoolId`.
  - `agentPoolId` is the Pulumi Deployments agent pool ID to run deployments on. Accept the default, `pulumi-provided-runners`, to use Pulumi Cloud hosted runners.
  - Change it later with `pulumi config set agentPoolId <value>`.
 
## Set up the Component Packages

The repo contains two component resource packages in separate folders. 
One abstracts the code for setting up the image, ECR and ECS deployment and the other abstracts the deploymnt settings.
Although the components can can be used as local components, for this exercise, it's recommended to manage it from a git repo.
In this case it is assumed to be in the same repo as the main program, but as noted below, components are best managed in their own, dedicated repos to allow fine grained control of versions.
 
From the Pulumi project folder created by `pulumi new`, run `pulumi package add` to install and set up the two component resource packages also included in this repo.

- Run `pulumi package add https://GITREPO-PATH-TO-COMPONENT/component-aws-container-services` 
  - Use the correct path to the componet folder.
    - If using version tags on the repo containing the component package, you can add `@vX.Y.Z` to the end of the path.

- Run `pulumi package add https://GITREPO-PATH-TO-COMPONENT/component-pulumi-deployment-settings` 
  - Use the correct path to the componet folder.
    - If using version tags on the repo containing the component package, you can add `@vX.Y.Z` to the end of the path.

The `pulumi package add` command performs the following tasks:
  - It adds a packages directive to the `Pulumi.yaml` file.
  - It creates an `sdks` folder which should **NOT** be committed to the repo.
  - It provdes the import line to add to `__main__.py` to reference the generated SDKs.
- SUBSEQUENTLY, you only need to run `pulumi install` which will use the `packages` directive in `Pulumi.yaml` to generate the local SDKs

## Version and Publish the Component Resources (optional)

The following steps are optional and not required to get started: 
- For versioning purposes, it is recommmended that a component is in its own repo. Then you can manage semantic versioning by adding tags to the repo of the form `vX.Y.Z`.
  - If in a separate repo, the `pulumi packages` reference needs to be updated to point to the repo and not local folder.
- Publish the package to the Pulumi component registry to be able to track usage of the and auto generate API docs.
  - `pulumi package publish GITREPO_PATH_TO_COMPONENNT --publisher PULUMI_ORG_NAME`
    - Where `GITREPO_PATH_TO_COMPONENT` is the same path used for the `pulumi package add` command.
    - Where `PULUMI_ORG_NAME` is the name of your Pulumi org.


# Runtime Prerequisites

Whereever `pulumi up` is run (laptop, deployment runner, etc) the following needs to be available:
- docker is running: Used to build the image pushed to ECR and deployed to ECS.
- AWS credentials/access with applicable permissions.
- Your preferred python tooling is available.

# Initializing and Bootstrapping Deployments

This project is set up such that it requires an initial pulumi up from a laptop to bootstrap the deployment settings using the deployment settings component resource.
In production, the deployment settings could be managed by a completely separate stack that manages the deployment settings for multiple stacks using the same sort of logic captured in the component resource.
But for ease of use, this initial boostrapping approach is used.

```bash
pulumi install
pulumi up
```




