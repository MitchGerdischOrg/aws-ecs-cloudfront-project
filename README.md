# aws-ecs-cloudfront-project
Pulumi project that deploys to ECS with a Cloudfront CDN and uses a component resource.

# Runtime Prerequisites

Where `pulumi up` is run (laptop, deployment runner, etc) the following needs to be available:
- docker is running: Used to build the image pushed to ECR and deployed to ECS.
- AWS credentials/access with applicable permissions.
- Your preferred python tooling is available.

# Set Up Steps

Clone/fork this repo to a github or other VCS account is connected to your Pulumi org. 
 
## aws-ecs-cloudfront-py

- Modify `Pulumi.yaml` as follows:
  - Replace `MitchllGerdisch` in the packages directive to reference the `component-aws-container-services-py` in your VCS repo.
    - (Optional) If versioning the component (see below), add `@vX.Y.Z` where `vX.Y.Z` matches the component's repository tag (including the `v`).
  - Modify the runtime options as per your preferred Python tooling if you don't use pip.

## component-aws-container-service
These are optional steps and not required to get started: 
- For versioning purposes, it is recommmended that a component is in its own repo. Then you can manage semantic versioning by adding tags to the repo of the form `vX.Y.Z`.
- Publish the package to the Pulumi component registry to be able to track usage of the and auto generate API docs.



