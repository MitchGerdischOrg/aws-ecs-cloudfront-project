# aws-ecs-cloudfront-project
Pulumi project that deploys to ECS with a Cloudfront CDN and uses a component resource.

# Set Up Steps

Clone/fork this repo to a github or other VCS account that is connected to your Pulumi org. 
 
## aws-ecs-cloudfront-py

- Modify `Pulumi.yaml` as follows:
  - Replace `MitchellGerdisch` in the packages directive to reference the `component-aws-container-services-py` in your VCS repo.
    - (Optional) If versioning the component (see below), add `@vX.Y.Z` where `vX.Y.Z` matches the component's repository tag (including the `v`).
  - Modify the runtime options as per your preferred Python tooling if you don't use pip.
- 

## component-aws-container-service
These are optional steps and not required to get started: 
- For versioning purposes, it is recommmended that a component is in its own repo. Then you can manage semantic versioning by adding tags to the repo of the form `vX.Y.Z`.
- Publish the package to the Pulumi component registry to be able to track usage of the and auto generate API docs.

# Runtime Prerequisites

Whereever `pulumi up` is run (laptop, deployment runner, etc) the following needs to be available:
- docker is running: Used to build the image pushed to ECR and deployed to ECS.
- AWS credentials/access with applicable permissions.
- Your preferred python tooling is available.

# Running from the Command Line

# Setting up Deployments

Before deployments can be configured, a stack needs to exist, so initialize a stack to start:
- Clone the repo
- `cd aws-ecs-cloudfront-py` 
- `pulumi stack init`

Deployment settings can be managed via the [Pulumi Service Provider](https://www.pulumi.com/registry/packages/pulumiservice/)
But to begin, it can be done by hand via the Pulumi Cloud UI.

Once the stack is initialized, navigate to the stack in teh Pulumi Cloud UI and configure the repo settings and if using customer managed runner, select the runner pool you want to use.
Additional settings can be configured for capabilities such as running preview on PRs and updates on merges, but are not needed to start.



