import json
import requests

def handler(event, context):
    try:
        print(f"Received Event: {json.dumps(event)}")  # Log full event data

        # Extract values from API Gateway Authorizer context
        api_key = event["requestContext"]["authorizer"].get("api_key", "N/A")
        target_url = event["requestContext"]["authorizer"].get("target_url", "N/A")
        provider_secret = event["requestContext"]["authorizer"].get("provider_secret", "N/A")

        print(f"Extracted from Authorizer - API Key: {api_key}, Target URL: {target_url}, Provider Secret: {provider_secret}")

        if provider_secret == "N/A" or target_url == "N/A":
            print("Error: Missing Provider Secret or Target URL")
            return {"statusCode": 403, "body": json.dumps({"error": "Unauthorized request"})}

        headers = {
            "Content-Type": "application/json",
            "X-Gateway-Key": provider_secret  # Attach secret key to forwarded request
        }

        print(f"Forwarding request to {target_url} with headers {headers}")

        # Forward request to Provider API
        response = requests.get(target_url, headers=headers)

        print(f"Received Response - Status: {response.status_code}, Body: {response.text}")

        return {"statusCode": response.status_code, "body": response.text}

    except Exception as e:
        print(f"Router Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal Server Error"})}