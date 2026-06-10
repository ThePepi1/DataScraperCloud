import ast
import hashlib
import io
import json
import os
import uuid
import boto3
import awswrangler as wr
import pandas as pd
from datetime import datetime, timezone

s3_client = boto3.client("s3")
BUCKET = os.environ["BUCKET_NAME"]
SILVER = "silver"


def normalise_ts(value):
    if not value or str(value).strip() in ("", "nan", "None"):
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def make_tweet_id(username, created_at, text):
    raw = f"{username}|{created_at}|{text}"
    return hashlib.sha256(raw.encode()).hexdigest()


def parse_hashtags(tags_field):
    if pd.isna(tags_field) or not str(tags_field).strip():
        return None
    raw = str(tags_field).strip()
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return json.dumps(parsed)
    except Exception:
        pass
    return raw or None


def handler(event, context):
    ingested_at = datetime.now(tz=timezone.utc).isoformat()
    tweet_rows = []
    user_rows = []
    seen_ids = set()

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if "bronze/twitter" not in key or not key.endswith(".csv"):
            print(f"Skipping: {key}")
            continue

        print(f"Processing: s3://{bucket}/{key}")
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        df_raw = pd.read_csv(io.BytesIO(obj["Body"].read()))

        for _, row in df_raw.iterrows():
            username = str(row.get("username", "") or "").strip()
            text = str(row.get("text", "") or "").strip()
            created_raw = str(row.get("date", "") or "").strip()
            created_at = normalise_ts(created_raw)

            tweet_id = make_tweet_id(username, created_raw, text)
            if tweet_id in seen_ids:
                continue
            seen_ids.add(tweet_id)

            is_retweet = bool(row.get("is_retweet", False))
            post_type = "retweet" if is_retweet else "tweet"

            year = month = day = None
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at)
                    year = str(dt.year)
                    month = str(dt.month).zfill(2)
                    day = str(dt.day).zfill(2)
                except Exception:
                    pass

            tweet_rows.append({
                "tweet_id": tweet_id,
                "author_username": username,
                "post_type": post_type,
                "content_text": text or None,
                "hashtags": parse_hashtags(row.get("hashtags")),
                "is_retweet": is_retweet,
                "created_at": created_at,
                "ingested_at": ingested_at,
                "year": year,
                "month": month,
                "day": day,
            })

            user_rows.append({
                "user_id": str(uuid.uuid4()),
                "username": username,
                "platform": "X",
                "karma_score": None,
                "is_verified": row.get("is_verified"),
                "created_at": normalise_ts(str(row.get("user_created_at", "") or "")),
                "ingested_at": ingested_at,
            })

    if tweet_rows:
        df_tweets = pd.DataFrame(tweet_rows)
        wr.s3.to_parquet(
            df=df_tweets,
            path=f"s3://{BUCKET}/{SILVER}/tweets/",
            dataset=True,
            mode="append",
            partition_cols=["year", "month", "day"],
            boto3_session=boto3.Session(),
        )
        print(f"[tweets] wrote {len(df_tweets)} rows")

    if user_rows:
        df_users = pd.DataFrame(user_rows).drop_duplicates(subset=["username"])
        wr.s3.to_parquet(
            df=df_users,
            path=f"s3://{BUCKET}/{SILVER}/users/",
            dataset=True,
            mode="append",
            partition_cols=["platform"],
            boto3_session=boto3.Session(),
        )
        print(f"[users/X] wrote {len(df_users)} rows")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "tweets": len(tweet_rows),
            "users": len(user_rows),
        }),
    }