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


def parse_hashtags(tags_field):
    if pd.isna(tags_field) or not str(tags_field).strip():
        return None
    raw = str(tags_field).strip()
    try:
        parsed = ast.literal_eval(raw)
        return json.dumps(parsed) if isinstance(parsed, list) else raw
    except:
        return raw


def get_existing_usernames(platform: str) -> set:
    try:
        df = wr.s3.read_parquet(
            path=f"s3://{BUCKET}/{SILVER}/users/",
            dataset=True,
            columns=["username"],
            filters=[("platform", "=", platform)],
            boto3_session=boto3.Session(),
        )
        return set(df["username"].tolist())
    except Exception:
        return set()


def handler(event, context):
    ingested_at = datetime.now(timezone.utc).isoformat()

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if "bronze/x" not in key and "bronze/twitter" not in key:
            print(f"Skipping: {key}")
            continue

        print(f"Processing: s3://{bucket}/{key}")
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(io.BytesIO(obj["Body"].read()))

        df["user_name"] = df["user_name"].fillna("").astype(str).str.strip()
        df["text"] = df["text"].fillna("").astype(str).str.strip()

        if "user_followers" in df.columns:
            df["user_followers"] = pd.to_numeric(df["user_followers"], errors="coerce").astype("Int64")
        else:
            df["user_followers"] = pd.NA

        raw_id = (df["user_name"] + "|" + df["date"].astype(str) + "|" + df["text"]).apply(
            lambda x: hashlib.sha256(x.encode()).hexdigest()
        )
        df["tweet_id"] = raw_id
        df = df.drop_duplicates(subset=["tweet_id"])

        df["created_at"] = df["date"].apply(normalise_ts)
        dt = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        df["year"] = dt.dt.year.astype("Int64").astype(str)
        df["month"] = dt.dt.month.astype("Int64").astype(str).str.zfill(2)
        df["day"] = dt.dt.day.astype("Int64").astype(str).str.zfill(2)

        df_tweets = df[[
            "tweet_id", "user_name", "is_retweet", "text",
            "hashtags", "user_followers", "created_at", "year", "month", "day"
        ]].copy()
        df_tweets.columns = [
            "tweet_id", "author_username", "is_retweet", "content_text",
            "hashtags", "followers", "created_at", "year", "month", "day"
        ]
        df_tweets["post_type"] = df_tweets["is_retweet"].map(lambda x: "retweet" if x else "tweet")
        df_tweets["ingested_at"] = ingested_at

        wr.s3.to_parquet(
            df=df_tweets,
            path=f"s3://{BUCKET}/{SILVER}/tweets/",
            dataset=True,
            mode="append",
            partition_cols=["year", "month", "day"],
            boto3_session=boto3.Session(),
        )
        print(f"[tweets] upisano {len(df_tweets)} redova")

        # Users
        df_users = df[[
            "user_name", "user_verified", "user_created", "user_followers"
        ]].drop_duplicates(subset=["user_name"]).copy()
        df_users.columns = ["username", "is_verified", "created_at", "followers"]
        df_users["user_id"] = [str(uuid.uuid4()) for _ in range(len(df_users))]
        df_users["platform"] = "X"
        df_users["karma_score"] = None
        df_users["ingested_at"] = ingested_at

        existing_usernames = get_existing_usernames("X")
        print(f"[users] postojećih X korisnika u S3: {len(existing_usernames)}")

        df_new_users = df_users[~df_users["username"].isin(existing_usernames)]

        if not df_new_users.empty:
            wr.s3.to_parquet(
                df=df_new_users,
                path=f"s3://{BUCKET}/{SILVER}/users/",
                dataset=True,
                mode="append",
                partition_cols=["platform"],
                boto3_session=boto3.Session(),
            )
            print(f"[users] upisano {len(df_new_users)} novih X korisnika")
        else:
            print("[users] nema novih X korisnika")

    return {"statusCode": 200}