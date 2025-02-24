import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

export class GatewayCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ✅ 1. Create a DynamoDB Table for API Keys
    const apiKeyTable = new dynamodb.Table(this, 'ApiKeyTable', {
      partitionKey: { name: 'api_key', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // ✅ 2. Create a Lambda Function for API Key Generation
    const createKeyLambda = new lambda.Function(this, 'CreateKeyLambda', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/create-key'),
      environment: {
        TABLE_NAME: apiKeyTable.tableName,
      },
    });

    // ✅ 3. Grant Lambda Permission to Write to DynamoDB
    apiKeyTable.grantWriteData(createKeyLambda);

    // ✅ 4. Create API Gateway
    const api = new apigateway.RestApi(this, 'ApiGateway', {
      restApiName: 'ApiGatewayPoc',
    });

    // ✅ 5. API Gateway Endpoint for API Key Creation
    const createKeyIntegration = new apigateway.LambdaIntegration(createKeyLambda);
    api.root.addResource('create-key').addMethod('POST', createKeyIntegration);
  }
}