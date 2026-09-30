"""Builds a simple container image, pushes it to ECR, runs it on ECS behind an ALB,
and fronts the ALB with a CloudFront distribution."""

import pulumi
import pulumi_aws as aws
import SEE_PACKAGE_INSTALL_INSTRUCTIONS as container_services
import SEE_PACKAGE_INSTALL_INSTRUCTIONS as deployment_settings


# Build the sample app image, push it to ECR, and deploy it to ECS behind an ALB.
app = container_services.AppImageDeploy(
    "app",
    docker_file_path="./app",
)

# AWS managed policies: CachingDisabled and AllViewer (forward all viewer request data).
CACHING_DISABLED_POLICY_ID = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
ALL_VIEWER_ORIGIN_REQUEST_POLICY_ID = "216adef6-5c7f-47e4-b989-5492eafa07d3"

# CloudFront distribution using the ALB as a custom origin.
# The ALB listener is HTTP only, so CloudFront talks to it over HTTP.
distribution = aws.cloudfront.Distribution(
    "app-cdn",
    enabled=True,
    comment="CloudFront in front of the ECS app ALB",
    origins=[
        aws.cloudfront.DistributionOriginArgs(
            origin_id="ecs-alb",
            domain_name=app.loadbalancer_dns_name,
            custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
                http_port=80,
                https_port=443,
                origin_protocol_policy="http-only",
                origin_ssl_protocols=["TLSv1.2"],
            ),
        )
    ],
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        target_origin_id="ecs-alb",
        viewer_protocol_policy="redirect-to-https",
        allowed_methods=[
            "GET",
            "HEAD",
            "OPTIONS",
            "PUT",
            "POST",
            "PATCH",
            "DELETE",
        ],
        cached_methods=["GET", "HEAD"],
        cache_policy_id=CACHING_DISABLED_POLICY_ID,
        origin_request_policy_id=ALL_VIEWER_ORIGIN_REQUEST_POLICY_ID,
    ),
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
        ),
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    ),
)

# Pulumi Deployments settings for this stack: preview on PRs and update on merges.
# Anything not set in stack config is worked out by the component:
#   repository     - 'owner/repo'; defaults to the local git 'origin' remote
#   branch         - defaults to the checked-out branch
#   repoDir        - defaults to this folder's path in the repo
#   agentPoolId    - defaults to Pulumi Cloud hosted runners
#   awsOidcRoleArn - AWS role to assume via OIDC; none by default
config = pulumi.Config()
deployment = deployment_settings.StackDeploymentSettings(
    "deployment-settings",
    repository=config.get("repository"),
    branch=config.get("branch"),
    repo_dir=config.get("repoDir"),
    agent_pool_id=config.get("agentPoolId"),
    aws_oidc_role_arn=config.get("awsOidcRoleArn"),
)

pulumi.export(
    "loadbalancer_url", pulumi.Output.concat("http://", app.loadbalancer_dns_name)
)
pulumi.export(
    "cloudfront_url", pulumi.Output.concat("https://", distribution.domain_name)
)
pulumi.export("deployment_settings_stack", deployment.stack_name)
