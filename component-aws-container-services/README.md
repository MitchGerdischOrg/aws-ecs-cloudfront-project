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
  container-services-py: https://github.com/pulumi-pequod/component-container-services-py@v1.0.0
```

Run `pulumi install` (or `pulumi package add https://github.com/pulumi-pequod/component-container-services-py@v1.0.0`) to generate the local SDK.

### Python

```python
import pulumi
import pulumi_pequod_container_services_py as container_services

app = container_services.AppImageDeploy(
    "app",
    docker_file_path="./app",
    cpu=256,      # optional, defaults to 256 (0.25 vCPU)
    memory=512,   # optional, defaults to 512 MiB
)

pulumi.export("url", pulumi.Output.concat("http://", app.loadbalancer_dns_name))
```

### YAML

```yaml
resources:
  app:
    type: container-services-py:AppImageDeploy
    properties:
      dockerFilePath: ./app
outputs:
  url: http://${app.loadbalancerDnsName}
```

## Inputs and outputs

| Component | Inputs | Outputs |
|-----------|--------|---------|
| `AppImage` | `dockerFilePath` (required) | `repositoryPath`, `imageRef` |
| `AppDeploy` | `imageReference` (required), `cpu`, `memory` | `loadbalancerDnsName` |
| `AppImageDeploy` | `dockerFilePath` (required), `cpu`, `memory` | `loadbalancerDnsName` |

## Development

```bash
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
pyright . && ruff check . && black --check .
pulumi package get-schema .
```
