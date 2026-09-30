"""AppImage: builds a Docker image and pushes it to a new, encrypted ECR repository."""

from typing import TypedDict

import pulumi
import pulumi_aws as aws
import pulumi_docker_build as docker_build

# Untagged images (e.g. superseded layers of the "latest" image) are expired after this many days.
_UNTAGGED_IMAGE_RETENTION_DAYS = 7


class AppImageArgs(TypedDict):
    docker_file_path: pulumi.Input[str]
    """The path to the directory containing the Dockerfile for the image to be built."""


class AppImage(pulumi.ComponentResource):
    repository_path: pulumi.Output[str]
    """The URI of the ECR repository that was created."""

    image_ref: pulumi.Output[str]
    """The image reference (URI) of the image that was built and pushed to the repository."""

    def __init__(
        self,
        name: str,
        args: AppImageArgs,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("container-services-py:index:AppImage", name, {}, opts)

        child_opts = pulumi.ResourceOptions(parent=self)
        tags = {"Owner": f"{pulumi.get_project()}-{pulumi.get_stack()}"}

        # Customer managed key used to encrypt the images at rest.
        kms_key = aws.kms.Key(
            f"{name}-kms-key",
            description="KMS key for encrypting ECR images",
            key_usage="ENCRYPT_DECRYPT",
            is_enabled=True,
            enable_key_rotation=True,
            deletion_window_in_days=7,
            tags=tags,
            opts=child_opts,
        )

        repository = aws.ecr.Repository(
            f"{name}-ecr-repo",
            encryption_configurations=[
                aws.ecr.RepositoryEncryptionConfigurationArgs(
                    encryption_type="KMS",
                    kms_key=kms_key.arn,
                )
            ],
            image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
                scan_on_push=True,
            ),
            # MUTABLE because we always push the "latest" tag.
            image_tag_mutability="MUTABLE",
            force_delete=True,
            tags=tags,
            opts=child_opts,
        )

        aws.ecr.LifecyclePolicy(
            f"{name}-ecr-lifecycle",
            repository=repository.name,
            policy=pulumi.Output.json_dumps(
                {
                    "rules": [
                        {
                            "rulePriority": 1,
                            "description": "Expire untagged images",
                            "selection": {
                                "tagStatus": "untagged",
                                "countType": "sinceImagePushed",
                                "countUnit": "days",
                                "countNumber": _UNTAGGED_IMAGE_RETENTION_DAYS,
                            },
                            "action": {"type": "expire"},
                        }
                    ]
                }
            ),
            opts=child_opts,
        )

        # Credentials used by the image build to push to ECR.
        auth = aws.ecr.get_authorization_token_output(
            registry_id=repository.registry_id
        )

        image = docker_build.Image(
            f"{name}-docker-image",
            # Use the docker buildx binary so builds work with Docker Build Cloud.
            exec_=True,
            # Use the pushed cache image as a cache source.
            cache_from=[
                docker_build.CacheFromArgs(
                    registry=docker_build.CacheFromRegistryArgs(
                        ref=pulumi.Output.concat(repository.repository_url, ":cache"),
                    )
                )
            ],
            cache_to=[
                docker_build.CacheToArgs(
                    registry=docker_build.CacheToRegistryArgs(
                        image_manifest=True,
                        oci_media_types=True,
                        ref=pulumi.Output.concat(repository.repository_url, ":cache"),
                    )
                )
            ],
            platforms=[docker_build.Platform.LINUX_AMD64],
            push=True,
            registries=[
                docker_build.RegistryArgs(
                    address=repository.repository_url,
                    username=auth.user_name,
                    password=auth.password,
                )
            ],
            tags=[pulumi.Output.concat(repository.repository_url, ":latest")],
            context=docker_build.BuildContextArgs(location=args["docker_file_path"]),
            opts=child_opts,
        )

        self.repository_path = repository.repository_url
        self.image_ref = image.ref

        self.register_outputs(
            {
                "repository_path": self.repository_path,
                "image_ref": self.image_ref,
            }
        )
