import json
import boto3
import uuid
import os
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.getenv("TABLE_NAME")
table = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    try:
        request_body = json.loads(event.get("body", "{}"))
        quota = request_body.get("quota", 10)  # Default quota = 10

        api_key = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        table.put_item(Item={
            "api_key": api_key,
            "quota_remaining": quota,
            "created_at": timestamp
        })

        return {
            "statusCode": 200,
            "body": json.dumps({
                "api_key": api_key,
                "quota": quota
            })
        }
    except Exception as e:
        print("Error:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to create API Key"})
        }