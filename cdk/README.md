# AWS CDK version (TypeScript)

The same stack as the CloudFormation version, written as a CDK app. `lib/stack.ts` defines the resources and reads the pipeline config from `../pipeline/pipeline.yaml`, putting the role's ARN in place of `SOURCE_ROLE_ARN`. It deploys as the stack `sample-log-routing`.

## Before you start

- Node.js and npm. CI uses Node.js 24.
- A CDK-bootstrapped account and Region. If you've never used CDK there, run this once:

  ```bash
  cd cdk && npm ci && npx cdk bootstrap
  ```

- The deploying role needs `iam:PassRole` for the pipeline's role and `logs:PutPipelineRule`.

## Deploy

```bash
cd cdk
npm ci
npx cdk diff      # optional: see what will be created
npx cdk deploy
```

The app has no settings. To change the routing, edit `pipeline/pipeline.yaml` and validate it first ([how](../README.md#check-the-config-first)).

## Outputs

`npx cdk deploy` prints `PipelineArn` and `PipelineRoleArn` when it finishes. Then [send logs through it](../README.md#send-logs-through-it).

## Clean up

Removing the pipeline needs `logs:DeletePipelineRule`. The log groups use `RemovalPolicy.DESTROY`, so this also deletes them and the events in them. From `cdk/`:

```bash
npx cdk destroy
```
