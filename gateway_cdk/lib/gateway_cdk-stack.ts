import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam'

export class GatewayCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ✅ 1. Create DynamoDB Table for API Keys & Quotas
    const apiKeyTable = new dynamodb.Table(this, 'ApiKeyTable', {
      partitionKey: { name: 'api_key', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // ✅ 2. Create DynamoDB Table for API Provider Mappings (Endpoint + Secret Key)
    const providerTable = new dynamodb.Table(this, 'ProviderTable', {
      partitionKey: { name: 'provider_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // ✅ 3. Create Lambda Function for API Key Issuance
    const createKeyLambda = new lambda.Function(this, 'CreateKeyLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/create-key'),
      environment: {
        API_KEY_TABLE: apiKeyTable.tableName,
        PROVIDER_TABLE: providerTable.tableName,
      },
    });

    // ✅ 4. Create the Hello World Lambda (Provider's API for Testing)
    const helloLambda = new lambda.Function(this, 'HelloLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/hello-world'),
    });

    // ✅ 5. Grant Lambda Permissions to Write to DynamoDB
    apiKeyTable.grantWriteData(createKeyLambda);
    providerTable.grantWriteData(createKeyLambda);

    // ✅ 6. Create Lambda Authorizer (Validates API Key + Quota + Fetches Provider Secret)
    const authorizerLambda = new lambda.Function(this, 'LambdaAuthorizer', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/authorizer'),
      environment: {
        API_KEY_TABLE: apiKeyTable.tableName,
        PROVIDER_TABLE: providerTable.tableName,
      },
    });

    // ✅ 7. Grant Lambda Permission to Read/Update DynamoDB
    apiKeyTable.grantReadWriteData(authorizerLambda);
    providerTable.grantReadWriteData(authorizerLambda);

    // ✅ 8. Create API Gateway
    const api = new apigateway.RestApi(this, 'ApiGateway', {
      restApiName: 'ApiGatewayPoc',
    });

    // ✅ 9. Attach Lambda Authorizer to API Gateway
    const authorizer = new apigateway.RequestAuthorizer(this, 'APIAuthorizer', {
      handler: authorizerLambda,
      identitySources: [apigateway.IdentitySource.header("Authorization")],
      resultsCacheTtl: cdk.Duration.seconds(0), // No caching for real-time quota updates
    });

    // ✅ 10. Create an API Gateway endpoint to expose HelloLambda (Unprotected for Now)
    const helloResource = api.root.addResource('hello');
    helloResource.addMethod('GET', new apigateway.LambdaIntegration(helloLambda));

    // ✅ 11. API Gateway Endpoint for API Key Creation (Unprotected)
    const createKeyIntegration = new apigateway.LambdaIntegration(createKeyLambda);
    api.root.addResource('create-key').addMethod('POST', createKeyIntegration);

    // ✅ 12. Create Lambda for Multi-Tenant Request Forwarding
    const routerLambda = new lambda.Function(this, 'RouterLambda', {
      runtime: lambda.Runtime.PYTHON_3_9,
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/router'), // NO BUNDLING!
      environment: {
        PROVIDER_TABLE: providerTable.tableName,
      },
    });

    // grant read access to ProviderTable
    providerTable.grantReadWriteData(routerLambda);

    // ✅ 13. API Gateway Protected Route (Forwards Request to Third-Party API)
    const providerResource = api.root.addResource('api').addResource('{provider_id}').addResource('invoke');
    providerResource.addMethod('POST', new apigateway.LambdaIntegration(routerLambda), {
      authorizationType: apigateway.AuthorizationType.CUSTOM,
      authorizer: authorizer,
    });


    const plan = api.addUsagePlan('DefaultUsagePlan', {
      name: 'BasicRateLimitPlan',
      throttle: {
        rateLimit: 10, // max 10 requests per second per user default
        burstLimit: 20, // allows short bursts of 20 requests default
      },
    });

    // ✅ Allow only API Gateway to invoke the Router Lambda
    routerLambda.addPermission('ApiGatewayInvoke', {
      principal: new iam.ServicePrincipal('apigateway.amazonaws.com'), // Only API Gateway can invoke it
      sourceArn: `${api.arnForExecuteApi()}` // Lock it to this API Gateway
    });
  }
}
