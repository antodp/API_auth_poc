import json

# Dummy secret key that the provider expects
VALID_GATEWAY_KEY = "secret-token-xyz"

def handler(event, context):
    print(f"Received Event: {json.dumps(event)}")

    # Extract headers from the incoming request
    headers = event.get("headers", {})
    received_key = headers.get("X-Gateway-Key", "")

    # Simulate authentication check
    if received_key != VALID_GATEWAY_KEY:
        print("Unauthorized Request: Invalid X-Gateway-Key")
        return {"statusCode": 403, "body": json.dumps({"message": "Unauthorized request"})}

    # If the key matches, return a successful response
    return {"statusCode": 200, "body": json.dumps({"message": "Hello, World!"})}