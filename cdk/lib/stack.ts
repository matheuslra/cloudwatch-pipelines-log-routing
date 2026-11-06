import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { Aws, CfnOutput, RemovalPolicy, Stack, StackProps, Tags } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as observabilityadmin from 'aws-cdk-lib/aws-observabilityadmin';
import { Construct } from 'constructs';

// A CloudWatch pipeline that parses a JSON envelope, runs Grok on the line inside it,
// and routes each event to a log group with its own retention.
export class LogRoutingStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const logGroup = (logicalId: string, logGroupName: string, retention: logs.RetentionDays) =>
      new logs.LogGroup(this, logicalId, { logGroupName, retention, removalPolicy: RemovalPolicy.DESTROY });

    // The pipeline finds this log group through its data source tags, which match
    // data_source_name and data_source_type in pipeline/pipeline.yaml.
    const source = logGroup('SourceLogGroup', '/sample/checkout/source', logs.RetentionDays.ONE_DAY);
    Tags.of(source).add('cw:datasource:name', 'checkout');
    Tags.of(source).add('cw:datasource:type', 'default');

    const destinations = [
      logGroup('AuditLogGroup', '/sample/checkout/audit', logs.RetentionDays.ONE_YEAR),
      logGroup('ErrorsLogGroup', '/sample/checkout/errors', logs.RetentionDays.ONE_MONTH),
      logGroup('DebugLogGroup', '/sample/checkout/debug', logs.RetentionDays.ONE_WEEK),
    ];

    const role = new iam.Role(this, 'PipelineRole', {
      assumedBy: new iam.ServicePrincipal('logs.amazonaws.com'),
      inlinePolicies: {
        'process-and-route': new iam.PolicyDocument({
          statements: [
            // Only for this data source, so the role can't process other log groups.
            new iam.PolicyStatement({
              actions: ['logs:ProcessWithPipeline'],
              resources: [
                `arn:${Aws.PARTITION}:logs:${Aws.REGION}:${Aws.ACCOUNT_ID}:log-group:/sample/checkout/source`,
                source.logGroupArn,
              ],
              conditions: {
                StringEquals: {
                  'aws:ResourceAccount': Aws.ACCOUNT_ID,
                  'logs:data_source_name': 'checkout',
                  'logs:data_source_type': 'default',
                },
              },
            }),
            // Routed destinations are authorized by this role, not by a log group resource policy.
            new iam.PolicyStatement({
              actions: ['logs:CreateLogStream', 'logs:PutLogEvents'],
              resources: destinations.map((group) => group.logGroupArn),
            }),
          ],
        }),
      },
    });

    const body = readFileSync(join(__dirname, '..', '..', 'pipeline', 'pipeline.yaml'), 'utf8')
      .replaceAll('SOURCE_ROLE_ARN', role.roleArn);

    const pipeline = new observabilityadmin.CfnTelemetryPipelines(this, 'Pipeline', {
      name: 'sample-checkout-routing',
      configuration: { body },
    });
    pipeline.node.addDependency(source, ...destinations);

    new CfnOutput(this, 'PipelineArn', { value: pipeline.attrArn });
    new CfnOutput(this, 'PipelineRoleArn', { value: role.roleArn });
  }
}
