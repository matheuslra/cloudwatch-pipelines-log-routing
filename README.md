# Route CloudWatch logs with chained parsers

Sample code for the blog post [Your Log Pipeline Is Now a Router](https://matheusarrais.com/blog/cloudwatch-pipelines-log-routing/).

A CloudWatch pipeline can replace the Lambda function behind a subscription filter. This one parses a JSON envelope, runs Grok on the line inside it, and routes each event to a log group with its own retention. The log groups and conditions are an example, so follow who reads your logs when you choose yours.

| Event | Log group | Retention |
| --- | --- | --- |
| `component` is `auth` | `/sample/checkout/audit` | 365 days |
| `level` is `ERROR`, any other component | `/sample/checkout/errors` | 30 days |
| Everything else | `/sample/checkout/debug` | 7 days |

## What gets deployed

The same stack is here three times. Pick one:

| Path | Tool |
| --- | --- |
| `cloudformation/template.yaml` | CloudFormation |
| `cdk/` | AWS CDK in TypeScript |
| `terraform/` | Terraform |

Each one creates:

- **The source log group** `/sample/checkout/source`, tagged `cw:datasource:name=checkout` and `cw:datasource:type=default`. Those tags are how the pipeline's `data_source_name` and `data_source_type` find it.
- **Three destination log groups,** each with its own retention.
- **The pipeline's role,** which CloudWatch Logs assumes. It can process only this data source and write only to the three destinations.
- **The pipeline** `sample-checkout-routing`, from `pipeline/pipeline.yaml`. The CDK app and the Terraform read that file. CloudFormation can't read a file, so the template has a copy, and CI fails if the two drift apart.

A data source name and type can belong to only one pipeline, so deploy one version at a time.

## Check the config first

These two calls create nothing in your account. Run them whenever you change `pipeline/pipeline.yaml`:

```bash
pip install -r scripts/requirements.txt
python scripts/pipeline.py validate
python scripts/pipeline.py test
```

`test` prints each sample event with the fields the parsers added. It doesn't show which route an event would take.

## Deploy

This creates real resources, and standard CloudWatch Logs charges apply. The caller needs `iam:PassRole` for the pipeline's role, and `logs:PutPipelineRule`.

**CloudFormation:**

```bash
aws cloudformation deploy --stack-name sample-log-routing \
  --template-file cloudformation/template.yaml --capabilities CAPABILITY_IAM
```

**CDK:**

```bash
cd cdk && npm ci && npx cdk deploy
```

**Terraform:**

```bash
cd terraform && terraform init && terraform apply
```

## Send logs through it

```bash
python scripts/send_sample_logs.py
```

It writes the four sample events to the source log group and prints the log group each one should land in. Then look at them:

```bash
aws logs tail /sample/checkout/audit --since 15m
aws logs tail /sample/checkout/errors --since 15m
aws logs tail /sample/checkout/debug --since 15m
```

## What I learned from the validator

- With a CloudWatch Logs source, `parse_json` rejects a `source` field, so this config uses `parse_json: {}`.
- The chain passes validation even though the [processor compatibility page](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/processor-compatibility.html) says parsers must come first.

## Before you use it

- **Processors change the event permanently,** and the raw log isn't kept. If you need the original line for audit, plan for that before adding parsers.
- **A pipeline allows up to 10 CloudWatch Logs sinks,** so design the route map with that limit in mind.
- **Routing alone won't lower your bill.** CloudWatch Logs sources are metered before processing, so the savings come from shorter retention on the noisy groups.
- **Keep credentials out of the config.** Pipeline definitions aren't encrypted with customer managed keys.

## Clean up

```bash
aws cloudformation delete-stack --stack-name sample-log-routing   # CloudFormation
npx cdk destroy                                                    # CDK, from cdk/
terraform destroy                                                  # Terraform, from terraform/
```

Removing the pipeline needs `logs:DeletePipelineRule`. All three versions also delete the log groups and the events in them.

## What was tested

- AWS accepted the config through `ValidateTelemetryPipelineConfiguration`, and `TestTelemetryPipeline` returned the expected fields for all four sample events.
- CI lints the CloudFormation template, checks its copy of the config, synthesizes the CDK app and validates the Terraform on every push. AWS's `ValidateTemplate` API accepted the template.
- I haven't deployed these stacks or sent real logs through them. The data source tags that connect the source log group to the pipeline come from the docs, so check that events reach the destinations before you build on it.

## Learn more

- [Route logs to multiple log groups](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/pipeline-sinks.html#cloudwatch-logs-sink-routing)
- [Data sources for custom logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/data-source-discovery-management.html)
- [Pipeline IAM reference](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/pipeline-iam-reference.html)
- [What's New announcement](https://aws.amazon.com/about-aws/whats-new/2026/10/cloudwatch-pipelines-log-routing/)

This is sample code for learning, not an official AWS project. Review it before you use it in your environment.

## License

[MIT-0](LICENSE)
