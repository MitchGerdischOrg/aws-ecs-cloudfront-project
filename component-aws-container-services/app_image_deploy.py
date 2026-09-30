"""AppImageDeploy: builds and pushes a Docker image, then deploys it, as a single component."""

from typing import TypedDict

import pulumi

from app_deploy import AppDeploy
from app_image import AppImage


class AppImageDeployArgs(TypedDict):
    docker_file_path: pulumi.Input[str]
    """The path to the directory containing the Dockerfile for the image to be built."""

    cpu: pulumi.Input[int] | None
    """The number of CPU units for the task, e.g. 256 (.25 vCPU), 512 (.5 vCPU), 1024 (1 vCPU)."""

    memory: pulumi.Input[int] | None
    """The amount of memory (in MiB) for the task, e.g. 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB)."""


class AppImageDeploy(pulumi.ComponentResource):
    loadbalancer_dns_name: pulumi.Output[str]
    """The DNS name at which the container's HTTP endpoint will be available."""

    def __init__(
        self,
        name: str,
        args: AppImageDeployArgs,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("container-services-py:index:AppImageDeploy", name, {}, opts)

        child_opts = pulumi.ResourceOptions(parent=self)

        image = AppImage(
            f"{name}-image",
            {"docker_file_path": args["docker_file_path"]},
            child_opts,
        )

        service = AppDeploy(
            f"{name}-deploy",
            {
                "image_reference": image.image_ref,
                "cpu": args.get("cpu"),
                "memory": args.get("memory"),
            },
            child_opts,
        )

        self.loadbalancer_dns_name = service.loadbalancer_dns_name

        self.register_outputs({"loadbalancer_dns_name": self.loadbalancer_dns_name})
