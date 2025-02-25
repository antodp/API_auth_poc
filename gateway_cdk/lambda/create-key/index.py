import json
import boto3
import uuid
import os

dynamodb = boto3.resource("dynamodb")
api_table = dynamodb.Table(os.getenv("API_KEY_TABLE"))
provider_table = dynamodb.Table(os.getenv("PROVIDER_TABLE"))

# Predefined provider secret key for the POC (since we assume only 1 provider)
STATIC_SECRET_KEY = "secret-token-xyz"
STATIC_PROVIDER_ID = "provider_1"

def handler(event, context):
    try:
        request_body = json.loads(event["body"])
        quota = request_body.get("quota")
        target_url = request_body.get("target_url")

        if not quota or not target_url:
            return {"statusCode": 400, "body": json.dumps({"error": "Quota and target_url required"})}

        # Generate a new API Key
        api_key = str(uuid.uuid4())

        # Store API Key & Quota in API Table
        api_table.put_item(Item={
            "api_key": api_key,
            "quota_remaining": quota,
            "target_url": target_url
        })

        # Store the provider’s secret key in the provider table (1 provider assumed)
        provider_table.put_item(Item={
            "provider_id": STATIC_PROVIDER_ID,
            "api_url": target_url,
            "secret_key": STATIC_SECRET_KEY
        })

        return {
            "statusCode": 200,
            "body": json.dumps({
                "api_key": api_key,
                "quota": quota,
                "provider_secret": STATIC_SECRET_KEY
            })
        }
    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error"})}