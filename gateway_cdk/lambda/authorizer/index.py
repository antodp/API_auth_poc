import json
import boto3
import os

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.getenv("TABLE_NAME")
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    try:
        # Extract API Key from headers
        headers = event.get("headers", {})
        api_key = headers.get("Authorization")

        if not api_key:
            return generate_policy("Deny", "Unauthorized: No API Key provided")

        # Fetch API Key from DynamoDB
        response = table.get_item(Key={"api_key": api_key})
        item = response.get("Item")

        if not item:
            return generate_policy("Deny", "Unauthorized: Invalid API Key")

        # Check if quota remains
        quota_remaining = int(item["quota_remaining"])
        if quota_remaining <= 0:
            return generate_policy("Deny", "Quota exceeded")

        # Allow access & update quota (Optional: update only after successful request)
        table.update_item(
            Key={"api_key": api_key},
            UpdateExpression="SET quota_remaining = quota_remaining - :dec",
            ExpressionAttributeValues={":dec": 1},
        )

        return generate_policy("Allow", "Authorized")

    except Exception as e:
        print("Error:", str(e))
        return generate_policy("Deny", "Internal Server Error")

def generate_policy(effect, message):
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": effect, "Resource": "*"}
            ],
        },
        "context": {"message": message},
    }