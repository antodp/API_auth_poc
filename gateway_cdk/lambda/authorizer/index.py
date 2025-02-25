import json
import boto3
import os

dynamodb = boto3.resource("dynamodb")
api_table = dynamodb.Table(os.getenv("API_KEY_TABLE"))
provider_table = dynamodb.Table(os.getenv("PROVIDER_TABLE"))

def generate_policy(effect, api_key, target_url, provider_secret):
    print(f"Generating Policy: Effect={effect}, API Key={api_key}, Target URL={target_url}, Secret={provider_secret}")
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": effect, "Resource": "*"}]
        },
        "context": {
            "api_key": api_key,
            "target_url": target_url,
            "provider_secret": provider_secret
        }
    }

def handler(event, context):
    print(f"Received Event: {json.dumps(event)}")

    try:
        token = event.get("headers", {}).get("Authorization", "")

        if not token:
            print("No API key found in request headers.")
            return generate_policy("Deny", "N/A", "N/A", "N/A")

        print(f"Fetching API Key: {token} from DynamoDB")
        response = api_table.get_item(Key={"api_key": token})

        if "Item" not in response:
            print(f"API Key {token} NOT found in DynamoDB!")
            return generate_policy("Deny", "N/A", "N/A", "N/A")

        api_data = response["Item"]
        quota_remaining = int(api_data.get("quota_remaining", 0))
        target_url = api_data.get("target_url", "N/A")

        print(f"API Key Found - Quota Remaining: {quota_remaining}, Target URL: {target_url}")

        if quota_remaining <= 0:
            print(f"API Key {token} has NO quota remaining!")
            return generate_policy("Deny", token, target_url, "N/A")

        # Fetch Provider secret key
        provider_response = provider_table.get_item(Key={"provider_id": "provider_1"})
        provider_data = provider_response.get("Item", {})
        provider_secret = provider_data.get("secret_key", "N/A")

        # ✅ **DECREASE QUOTA in DynamoDB**
        print(f"Decreasing quota for API Key: {token}")
        api_table.update_item(
            Key={"api_key": token},
            UpdateExpression="SET quota_remaining = quota_remaining - :decr",
            ExpressionAttributeValues={":decr": 1}
        )

        return generate_policy("Allow", token, target_url, provider_secret)

    except Exception as e:
        print(f"Error in Authorizer: {str(e)}")
        return generate_policy("Deny", "N/A", "N/A", "N/A")