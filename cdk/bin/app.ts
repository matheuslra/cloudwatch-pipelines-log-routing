import { App } from 'aws-cdk-lib';
import { LogRoutingStack } from '../lib/stack';

const app = new App();
new LogRoutingStack(app, 'LogRouting', { stackName: 'sample-log-routing' });
