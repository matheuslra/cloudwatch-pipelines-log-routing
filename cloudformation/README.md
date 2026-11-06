# CloudFormation version

One template, `template.yaml`, deployed with the AWS CLI. It creates everything listed in the [main README](../README.md#what-gets-deployed): the source log group with its data source tags, the three destination log groups, the pipeline's role and the pipeline.

CloudFormation can't read another file, so the template carries its own copy of the pipeline config from `pipeline/pipeline.yaml`, inline under `Configuration.Body`. CI fails if the two copies drift apart, so change both together.

## Deploy

The caller needs `iam:PassRole` for the pipeline's role and `logs:PutPipelineRule`.

```bash
aws cloudformation deploy --stack-name sample-log-routing \
  --template-file cloudformation/template.yaml --capabilities CAPABILITY_IAM
```

`CAPABILITY_IAM` is needed because the stack creates the role that CloudWatch Logs assumes to run the pipeline. The template has no parameters.

## Outputs

`PipelineArn` and `PipelineRoleArn`:

```bash
aws cloudformation describe-stacks --stack-name sample-log-routing --query 'Stacks[0].Outputs' --output table
```

Then [send logs through it](../README.md#send-logs-through-it).

## Clean up

Removing the pipeline needs `logs:DeletePipelineRule`. This also deletes the log groups and the events in them.

```bash
aws cloudformation delete-stack --stack-name sample-log-routing
aws cloudformation wait stack-delete-complete --stack-name sample-log-routing
```
