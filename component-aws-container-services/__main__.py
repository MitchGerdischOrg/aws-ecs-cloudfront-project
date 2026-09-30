"""Entry point that hosts the container-services-py component provider."""

from pulumi.provider.experimental import component_provider_host

from app_deploy import AppDeploy
from app_image import AppImage
from app_image_deploy import AppImageDeploy

if __name__ == "__main__":
    component_provider_host(
        name="container-services",
        components=[AppImage, AppDeploy, AppImageDeploy],
    )
