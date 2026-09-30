# component-container-services-py

A Python multi-language Pulumi component package that abstracts the resources needed to run a container on AWS:

- `AppImage`: builds a Docker image and pushes it to a new, KMS-encrypted ECR repository.
- `AppDeploy`: runs an image on ECS Fargate behind an internet-facing Application Load Balancer in the default VPC. The service only accepts traffic from the load balancer.
- `AppImageDeploy`: does both of the above as a single component.

This is a Python implementation of `component-container-services`. It uses `pulumi-aws` and `pulumi-docker-build` directly (no `awsx`), and all resources are children of the component.

The container is expected to listen on port 80.

## Usage

### Add the package to `Pulumi.yaml`

```
packages:
  # versioning is optional
  container-services-py: https://GITREPO-PATH/component-aws-container-services[@v1.0.0]
```

Run `pulumi install` (or `pulumi package add https://GITREPO-PATH/component-aws-container-services[@v1.0.0]` - version is optional) to generate the local SDK.

These commands will also provide the python import code for referencing the component.

### Python

```python
import pulumi
import XXXX_aws_container_services_py as container_services

app = container_services.AppImageDeploy(
    "app",
    docker_file_path="./app",
    cpu=256,      # optional, defaults to 256 (0.25 vCPU)
    memory=512,   # optional, defaults to 512 MiB
)

pulumi.export("url", pulumi.Output.concat("http://", app.loadbalancer_dns_name))
```

## Inputs and outputs

| Component | Inputs | Outputs |
|-----------|--------|---------|
| `AppImage` | `dockerFilePath` (required) | `repositoryPath`, `imageRef` |
| `AppDeploy` | `imageReference` (required), `cpu`, `memory` | `loadbalancerDnsName` |
| `AppImageDeploy` | `dockerFilePath` (required), `cpu`, `memory` | `loadbalancerDnsName` |

