"""AppDeploy: runs a container image on ECS Fargate behind an internet-facing ALB."""

from typing import TypedDict

import pulumi
import pulumi_aws as aws

# The port the container listens on.
_CONTAINER_PORT = 80
_DEFAULT_CPU = 256  # 0.25 vCPU
_DEFAULT_MEMORY = 512  # 0.5 GB
_LOG_RETENTION_DAYS = 7


class AppDeployArgs(TypedDict):
    image_reference: pulumi.Input[str]
    """The registry reference for the image to deploy. Required."""

    cpu: pulumi.Input[int] | None
    """The number of CPU units for the task, e.g. 256 (.25 vCPU), 512 (.5 vCPU), 1024 (1 vCPU)."""

    memory: pulumi.Input[int] | None
    """The amount of memory (in MiB) for the task, e.g. 512 (0.5 GB), 1024 (1 GB), 2048 (2 GB)."""


class AppDeploy(pulumi.ComponentResource):
    loadbalancer_dns_name: pulumi.Output[str]
    """The DNS name at which the container's HTTP endpoint will be available."""

    def __init__(
        self,
        name: str,
        args: AppDeployArgs,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("container-services-py:index:AppDeploy", name, {}, opts)

        child_opts = pulumi.ResourceOptions(parent=self)
        tags = {"Owner": f"{pulumi.get_project()}-{pulumi.get_stack()}"}

        # Fargate takes cpu/memory as strings; the args may be plain values or Outputs.
        cpu_arg = args.get("cpu")
        memory_arg = args.get("memory")
        cpu = pulumi.Output.from_input(
            _DEFAULT_CPU if cpu_arg is None else cpu_arg
        ).apply(str)
        memory = pulumi.Output.from_input(
            _DEFAULT_MEMORY if memory_arg is None else memory_arg
        ).apply(str)

        # Networking: use the default VPC and its subnets.
        vpc = aws.ec2.get_vpc_output(default=True)
        subnets = aws.ec2.get_subnets_output(
            filters=vpc.id.apply(
                lambda vpc_id: [
                    aws.ec2.GetSubnetsFilterArgs(name="vpc-id", values=[vpc_id])
                ]
            )
        )

        # ALB that serves the container endpoint to the internet.
        lb_security_group = aws.ec2.SecurityGroup(
            f"{name}-lb-sg",
            vpc_id=vpc.id,
            description="Allow HTTP to the load balancer",
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=80,
                    to_port=80,
                    cidr_blocks=["0.0.0.0/0"],
                    description="HTTP from anywhere",
                )
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    protocol="-1",
                    from_port=0,
                    to_port=0,
                    cidr_blocks=["0.0.0.0/0"],
                    description="All outbound",
                )
            ],
            tags=tags,
            opts=child_opts,
        )

        loadbalancer = aws.lb.LoadBalancer(
            f"{name}-lb",
            load_balancer_type="application",
            internal=False,
            subnets=subnets.ids,
            security_groups=[lb_security_group.id],
            tags=tags,
            opts=child_opts,
        )

        target_group = aws.lb.TargetGroup(
            f"{name}-tg",
            port=_CONTAINER_PORT,
            protocol="HTTP",
            target_type="ip",
            vpc_id=vpc.id,
            tags=tags,
            opts=child_opts,
        )

        listener = aws.lb.Listener(
            f"{name}-listener",
            load_balancer_arn=loadbalancer.arn,
            port=80,
            protocol="HTTP",
            default_actions=[
                aws.lb.ListenerDefaultActionArgs(
                    type="forward",
                    target_group_arn=target_group.arn,
                )
            ],
            opts=child_opts,
        )

        # ECS cluster and the roles/logging the Fargate task needs.
        cluster = aws.ecs.Cluster(f"{name}-ecs", tags=tags, opts=child_opts)

        execution_role = aws.iam.Role(
            f"{name}-execution-role",
            assume_role_policy=aws.iam.get_policy_document_output(
                statements=[
                    aws.iam.GetPolicyDocumentStatementArgs(
                        actions=["sts:AssumeRole"],
                        principals=[
                            aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                                type="Service",
                                identifiers=["ecs-tasks.amazonaws.com"],
                            )
                        ],
                    )
                ]
            ).json,
            tags=tags,
            opts=child_opts,
        )
        execution_role_policy = aws.iam.RolePolicyAttachment(
            f"{name}-execution-role-policy",
            role=execution_role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
            opts=child_opts,
        )

        log_group = aws.cloudwatch.LogGroup(
            f"{name}-logs",
            retention_in_days=_LOG_RETENTION_DAYS,
            tags=tags,
            opts=child_opts,
        )

        container_name = f"{name}-container"
        task_definition = aws.ecs.TaskDefinition(
            f"{name}-task",
            family=f"{name}-task",
            cpu=cpu,
            memory=memory,
            network_mode="awsvpc",
            requires_compatibilities=["FARGATE"],
            execution_role_arn=execution_role.arn,
            container_definitions=pulumi.Output.json_dumps(
                [
                    {
                        "name": container_name,
                        "image": args["image_reference"],
                        "essential": True,
                        "portMappings": [
                            {"containerPort": _CONTAINER_PORT, "protocol": "tcp"}
                        ],
                        "logConfiguration": {
                            "logDriver": "awslogs",
                            "options": {
                                "awslogs-group": log_group.name,
                                "awslogs-region": aws.get_region_output().region,
                                "awslogs-stream-prefix": name,
                            },
                        },
                    }
                ]
            ),
            tags=tags,
            opts=pulumi.ResourceOptions(
                parent=self, depends_on=[execution_role_policy]
            ),
        )

        # Only the load balancer may reach the container.
        service_security_group = aws.ec2.SecurityGroup(
            f"{name}-service-sg",
            vpc_id=vpc.id,
            description="Allow HTTP from the load balancer to the service",
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=_CONTAINER_PORT,
                    to_port=_CONTAINER_PORT,
                    security_groups=[lb_security_group.id],
                    description="HTTP from the load balancer",
                )
            ],
            egress=[
                aws.ec2.SecurityGroupEgressArgs(
                    protocol="-1",
                    from_port=0,
                    to_port=0,
                    cidr_blocks=["0.0.0.0/0"],
                    description="All outbound (image pulls, logs)",
                )
            ],
            tags=tags,
            opts=child_opts,
        )

        aws.ecs.Service(
            f"{name}-service",
            cluster=cluster.arn,
            task_definition=task_definition.arn,
            desired_count=1,
            launch_type="FARGATE",
            network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                assign_public_ip=True,
                subnets=subnets.ids,
                security_groups=[service_security_group.id],
            ),
            load_balancers=[
                aws.ecs.ServiceLoadBalancerArgs(
                    target_group_arn=target_group.arn,
                    container_name=container_name,
                    container_port=_CONTAINER_PORT,
                )
            ],
            tags=tags,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[listener]),
        )

        self.loadbalancer_dns_name = loadbalancer.dns_name

        self.register_outputs({"loadbalancer_dns_name": self.loadbalancer_dns_name})
