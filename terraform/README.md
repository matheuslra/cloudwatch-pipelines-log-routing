# Terraform version

The same stack as the CloudFormation version, in Terraform, using the `hashicorp/aws` provider 6.60 or later for `aws_observabilityadmin_telemetry_pipeline`. It reads the pipeline config from `../pipeline/pipeline.yaml` and puts the role's ARN in place of `SOURCE_ROLE_ARN`.

## Before you start

- Terraform 1.6 or later.
- AWS credentials for the target account, for example `export AWS_PROFILE=my-test-account`. The caller needs `iam:PassRole` for the pipeline's role and `logs:PutPipelineRule`.

## Deploy

```bash
cd terraform
terraform init
terraform plan    # optional: see what will be created
terraform apply
```

| Variable | Default | What it does |
| --- | --- | --- |
| `region` | `us-east-1` | Where to deploy. Use a Region where CloudWatch pipelines is generally available |

To change the routing, edit `pipeline/pipeline.yaml` and validate it first ([how](../README.md#check-the-config-first)).

## Outputs

```bash
terraform output
```

That lists `pipeline_arn` and `pipeline_role_arn`. Then [send logs through it](../README.md#send-logs-through-it).

## Clean up

Removing the pipeline needs `logs:DeletePipelineRule`. This also deletes the log groups and the events in them. From `terraform/`:

```bash
terraform destroy
```
