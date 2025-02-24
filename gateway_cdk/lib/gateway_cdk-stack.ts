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

    // ✅ 2. Create Lambda for API Key Issuance
    const createKeyLambda = new lambda.Function(this, 'CreateKeyLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/create-key'),
      environment: {
        TABLE_NAME: apiKeyTable.tableName,
      },
    });

    apiKeyTable.grantWriteData(createKeyLambda);

    // ✅ 3. Create Lambda Authorizer
    const authorizerLambda = new lambda.Function(this, 'LambdaAuthorizer', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/authorizer'),
      environment: {
        TABLE_NAME: apiKeyTable.tableName,
      },
    });

    apiKeyTable.grantReadWriteData(authorizerLambda);

    // ✅ 4. Create API Gateway
    const api = new apigateway.RestApi(this, 'ApiGateway', {
      restApiName: 'ApiGatewayPoc',
    });

    // ✅ 5. Attach Lambda Authorizer to API Gateway
    const authorizer = new apigateway.RequestAuthorizer(this, 'APIAuthorizer', {
      handler: authorizerLambda,
      identitySources: [apigateway.IdentitySource.header("Authorization")],
      resultsCacheTtl: cdk.Duration.seconds(0), // No caching for real-time quota updates
    });

    // ✅ 6. API Gateway Endpoint for API Key Creation (Unprotected)
    const createKeyIntegration = new apigateway.LambdaIntegration(createKeyLambda);
    api.root.addResource('create-key').addMethod('POST', createKeyIntegration);

    // ✅ 7. Deploy Dummy "Hello World" API with Authorization
    const helloLambda = new lambda.Function(this, 'HelloLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/hello-world'),
    });

    const helloIntegration = new apigateway.LambdaIntegration(helloLambda);
    const helloResource = api.root.addResource('hello');
    helloResource.addMethod('GET', helloIntegration, {
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      authorizer: authorizer,
    });
  }
}