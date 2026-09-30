# aws-ecs-cloudfront-project
Pulumi project that deploys to ECS with a Cloudfront CDN and uses a component resource.

# Set Up Steps

Clone/fork this repo to a github or other VCS account that is connected to your Pulumi org. 
 
## aws-ecs-cloudfront-py
 
This folder contains a component resource package that abstracts the code for setting up the image, ECR and ECS deployment.
Although it can be used as a local component, for this exercise, it's recommended to manage it from a git repo.
In this case it is assumed to be in the same repo as the main program, but as noted below, components are best managed in their own, dedicated repos to allow fine grained control of versions.
 
- Run `pulumi package add https://GITREPO-PATH-TO-COMPONENT/component-aws-container-services` 
  - Use the correct path to the componet folder.
    - If using version tags on the repo containing the component package, you can add `@vX.Y.Z` to the end of the path.

- Run `pulumi package add https://GITREPO-PATH-TO-COMPONENT/component-pulumi-deployment-settings` 
  - Use the correct path to the componet folder.
    - If using version tags on the repo containing the component package, you can add `@vX.Y.Z` to the end of the path.

The `pulumi package add` command performs the following tasks:
  - It adds a packages directive to the `Pulumi.yaml` file.
  - It creates an `sdks` folder which should NOT be committed to the repo.
  - It provdes the import line for `__main__.py` to reference the generated SDKs.
- SUBSEQUENTLY, you only need to run `pulumi install` which will use the `packages` directive in `Pulumi.yaml` to generate the local SDKs

## component-aws-container-service

This component abstracts the creation of the docker image, pushing it to ECR and deploying it to ECS.

The following steps are optional and not required to get started: 
- For versioning purposes, it is recommmended that a component is in its own repo. Then you can manage semantic versioning by adding tags to the repo of the form `vX.Y.Z`.
  - If in a separate repo, the `pulumi packages` reference needs to be updated to point to the repo and not local folder.
- Publish the package to the Pulumi component registry to be able to track usage of the and auto generate API docs.
  - `pulumi package publish GITREPO_PATH_TO_COMPONENNT --publisher PULUMI_ORG_NAME`
    - Where `GITREPO_PATH_TO_COMPONENT` is the same path used for the `pulumi package add` command.
    - Where `PULUMI_ORG_NAME` is the name of your Pulumi org.

## component-pulumi-deployment-settings

This component abstracts the configuration of the stack's deployment settings.

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




