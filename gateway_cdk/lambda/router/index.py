import json
import boto3
import os
import requests

dynamodb = boto3.resource("dynamodb")
provider_table = dynamodb.Table(os.getenv("PROVIDER_TABLE"))

def handler(event, context):
    print(f"Received Event: {json.dumps(event)}")

    provider_id = event.get("pathParameters", {}).get("provider_id", "")

    if not provider_id:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing provider_id"})}

    # Lookup provider details in DynamoDB
    response = provider_table.get_item(Key={"provider_id": provider_id})
    print(f"DynamoDB Response: {json.dumps(response)}")

    if "Item" not in response:
        return {"statusCode": 404, "body": json.dumps({"error": "Provider not found"})}

    provider_data = response["Item"]
    print(f"Provider Data Retrieved: {json.dumps(provider_data)}")

    # 🔹 Fix: Ensure "api_url" exists
    if "api_url" not in provider_data:
        return {"statusCode": 500, "body": json.dumps({"error": "Missing api_url in provider data"})}

    target_url = provider_data["api_url"]
    provider_secret = provider_data["secret_key"]
    expected_method = provider_data.get("expected_method", "GET")  # ✅ Default to GET if missing

    # Extract user API key from headers
    headers = event.get("headers", {}).copy()
    # headers.pop("Authorization", None)  # 🔹 Remove AWS-sensitive header
    headers["X-Gateway-Key"] = provider_secret  # 🔹 Authenticate request at provider's side

    # 🔹 Ensure correct HTTP method
    method = expected_method

    # logging
    print(f"Forwarding request to: {target_url}")
    print(f"Using method: {method}")
    print(f"Headers: {headers}")

    # Forward request using the provider's expected method
    try:
        if method == "GET":
            response = requests.get(target_url, headers=headers)
        elif method == "POST":
            response = requests.post(target_url, headers=headers, json=event.get("body", {}))
        elif method == "PUT":
            response = requests.put(target_url, headers=headers, json=event.get("body", {}))
        elif method == "DELETE":
            response = requests.delete(target_url, headers=headers)
        else:
            return {"statusCode": 400, "body": json.dumps({"error": f"Unsupported method {method}"})}

        return {"statusCode": response.status_code, "body": response.text}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error"})}