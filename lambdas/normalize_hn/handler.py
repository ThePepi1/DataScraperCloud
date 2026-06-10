import json
import os
import re
import uuid
import boto3
import awswrangler as wr
import pandas as pd
from datetime import datetime, timezone
from html.parser import HTMLParser

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_NAME"]
SILVER = "silver"


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def strip_html(text):
    if not text:
        return None
    s = _HTMLStripper()
    s.feed(text)
    result = " ".join(s.parts).strip()
    return re.sub(r"\s+", " ", result) or None


def normalise_ts(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return value


def get_hn_type(tags):
    if "job" in tags:
        return "job"
    if "poll" in tags:
        return "poll"
    if "comment" in tags:
        return "comment"
    if "ask_hn" in tags:
        return "ask_hn"
    if "show_hn" in tags:
        return "show_hn"
    return "story"


def process_record(item):
    tags = item.get("_tags", [])
    hn_type = get_hn_type(tags)
    author = item.get("author")
    created_at = normalise_ts(item.get("created_at_i") or item.get("created_at"))
    object_id = str(item.get("objectID", ""))

    year = month = day = None
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at)
            year = str(dt.year)
            month = str(dt.month).zfill(2)
            day = str(dt.day).zfill(2)
        except Exception:
            pass

    base = {
        "post_id": object_id,
        "author_username": author,
        "post_type": hn_type,
        "created_at": created_at,
        "ingested_at": datetime.now(tz=timezone.utc).isoformat(),
        "year": year,
        "month": month,
        "day": day,
    }

    if hn_type == "job":
        return {**base, "title": item.get("title"), "url": item.get("url"),
                "content_text": None, "parent_id": None, "story_id": None,
                "points": None, "num_comments": None}

    if hn_type == "poll":
        return {**base, "title": item.get("title"), "content_text": None,
                "url": None, "parent_id": None, "story_id": None,
                "points": item.get("points"), "num_comments": item.get("num_comments")}

    if hn_type == "comment":
        return {**base, "title": None,
                "content_text": strip_html(item.get("comment_text")),
                "url": None,
                "parent_id": str(item.get("parent_id", "")),
                "story_id": str(item.get("story_id", "")),
                "points": item.get("points"), "num_comments": None}

    return {**base, "title": item.get("title"),
            "content_text": strip_html(item.get("story_text")),
            "url": item.get("url"), "parent_id": None, "story_id": None,
            "points": item.get("points"), "num_comments": item.get("num_comments")}


def record_to_user(item):
    author = item.get("author")
    if not author:
        return None
    return {
        "user_id": str(uuid.uuid4()),
        "username": author,
        "platform": "HackerNews",
        "karma_score": None,
        "is_verified": None,
        "created_at": None,
        "ingested_at": datetime.now(tz=timezone.utc).isoformat(),
    }


def get_existing_usernames(platform: str) -> set:
    """Čita samo username kolonu iz S3 za datu platformu."""
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
        # Tabela još ne postoji
        return set()


def write_table(rows, table, partition_cols):
    if not rows:
        return
    df = pd.DataFrame(rows)
    wr.s3.to_parquet(
        df=df,
        path=f"s3://{BUCKET}/{SILVER}/{table}/",
        dataset=True,
        mode="append",
        partition_cols=partition_cols,
        boto3_session=boto3.Session(),
    )
    print(f"[{table}] wrote {len(df)} rows")


def handler(event, context):
    posts_rows = []
    jobs_rows = []
    polls_rows = []
    users_rows = []
    seen_ids = set()

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        if "bronze/hackernews" not in key or not key.endswith(".json"):
            print(f"Skipping: {key}")
            continue

        print(f"Processing: s3://{bucket}/{key}")
        obj = s3.get_object(Bucket=bucket, Key=key)
        items = json.loads(obj["Body"].read())

        for item in items:
            oid = str(item.get("objectID", ""))
            if oid in seen_ids:
                continue
            seen_ids.add(oid)

            processed = process_record(item)
            hn_type = processed["post_type"]

            user = record_to_user(item)
            if user:
                users_rows.append(user)

            if hn_type == "job":
                jobs_rows.append(processed)
            elif hn_type == "poll":
                polls_rows.append(processed)
            else:
                posts_rows.append(processed)

    date_parts = ["year", "month", "day"]
    write_table(posts_rows, "posts", date_parts)
    write_table(jobs_rows, "jobs", date_parts)
    write_table(polls_rows, "polls", date_parts)

    if users_rows:
        # 1. Deduplikacija unutar batch-a
        df_users = pd.DataFrame(users_rows).drop_duplicates(subset=["username"])

        # 2. Učitaj postojeće username-ove iz S3 (samo ta kolona)
        existing_usernames = get_existing_usernames("HackerNews")
        print(f"[users] postojećih u S3: {len(existing_usernames)}")

        # 3. Zadrži samo one kojih nema u S3
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
            print(f"[users] upisano {len(df_new_users)} novih korisnika")
        else:
            print("[users] nema novih korisnika")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "posts": len(posts_rows),
            "jobs": len(jobs_rows),
            "polls": len(polls_rows),
            "users": len(users_rows),
        }),
    }