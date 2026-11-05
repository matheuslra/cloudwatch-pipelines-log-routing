# Route CloudWatch logs with chained parsers

Sample code for the blog post [Your Log Pipeline Is Now a Router](https://matheusarrais.com/blog/cloudwatch-pipelines-log-routing/).

A CloudWatch pipeline can replace the Lambda function behind a subscription filter. This one parses a JSON envelope, runs Grok on the line inside it, and routes each event to a log group with its own retention. The log groups and conditions are an example, so follow who reads your logs when you choose yours.

| Event | Log group | Retention |
| --- | --- | --- |
| `component` is `auth` | `/sample/checkout/audit` | 365 days |
| `level` is `ERROR`, any other component | `/sample/checkout/errors` | 30 days |
| Everything else | `/sample/checkout/debug` | 7 days |

## What's here

| Path | What it does |
| --- | --- |
| `pipeline/pipeline.yaml` | The pipeline: two parsers, three routes |
| `infra/resources.yaml` | CloudFormation for the log groups and the pipeline's role |
| `scripts/pipeline.py` | Validates, tests or creates the pipeline |
| `local/check_config.py` | Offline check of limits, route fields and the expected route of each sample |
| `samples/` | Sample events and the route each should take |

## Try it with no AWS account

```bash
pip install -r local/requirements.txt
./local/smoke-test.sh
```

The offline check uses a small stand-in for Grok and the `when` syntax, so it only understands what this sample uses.

## Test it against AWS

These two calls create nothing in your account:

```bash
pip install -r scripts/requirements.txt
python scripts/pipeline.py validate
python scripts/pipeline.py test
```

`test` prints each event with the fields the parsers added. It doesn't show which route an event would take, which is why the offline check exists.

## Create it

This creates real resources, and standard CloudWatch Logs charges apply.

```bash
aws cloudformation deploy --stack-name sample-log-routing --template-file infra/resources.yaml --capabilities CAPABILITY_IAM
python scripts/pipeline.py create --role-arn <PipelineRoleArn output>
```

The caller needs `iam:PassRole` for the role and `logs:PutPipelineRule`. To remove everything, delete the pipeline and then the stack.

## What was tested

- AWS accepted this config through `ValidateTelemetryPipelineConfiguration`, and `TestTelemetryPipeline` returned the expected fields for all four sample events.
- I have not created this pipeline or sent real logs through it, so the routes and the role are untested end to end. I also haven't confirmed how a custom log group's events get matched to `data_source_name`, so check that first.

## What I learned from the validator

- With a CloudWatch Logs source, `parse_json` rejects a `source` field, so this config uses `parse_json: {}`.
- The chain passes validation even though the [processor compatibility page](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/processor-compatibility.html) says parsers must come first.

## Learn more

- [Route logs to multiple log groups](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/pipeline-sinks.html#cloudwatch-logs-sink-routing)
- [Pipeline IAM reference](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/pipeline-iam-reference.html)
- [What's New announcement](https://aws.amazon.com/about-aws/whats-new/2026/10/cloudwatch-pipelines-log-routing/)

This is sample code for learning, not an official AWS project. Review it before you use it in your environment.

## License

[MIT-0](LICENSE)
