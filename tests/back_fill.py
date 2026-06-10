import boto3
import json

s3 = boto3.client("s3", region_name="eu-central-1")
lambda_client = boto3.client("lambda", region_name="eu-central-1")

BUCKET = "social-media-data-lake-916868258494"

paginator = s3.get_paginator("list_objects_v2")
pages = paginator.paginate(Bucket=BUCKET, Prefix="bronze/hackernews/")

for page in pages:
    for obj in page.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".json"):
            continue

        print(f"Okidam: {key}")
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": BUCKET},
                        "object": {"key": key}
                    }
                }
            ]
        }
        lambda_client.invoke(
            FunctionName="normalize_hn_lambda",
            InvocationType="Event",
            Payload=json.dumps(event)
        )

pages = paginator.paginate(Bucket=BUCKET, Prefix="bronze/twitter/")

for page in pages:
    for obj in page.get("Contents", []):
        key = obj["Key"]
        if not key.endswith(".csv"):
            continue

        print(f"Okidam: {key}")
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": BUCKET},
                        "object": {"key": key}
                    }
                }
            ]
        }
        lambda_client.invoke(
            FunctionName="normalize_twitter_lambda",
            InvocationType="Event",
            Payload=json.dumps(event)
        )

print("Gotovo!")