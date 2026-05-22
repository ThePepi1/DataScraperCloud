import json

def handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from the Bronze Layer Lambda!')
    }