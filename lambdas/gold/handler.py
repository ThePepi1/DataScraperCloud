import os
import json
import boto3
import awswrangler as wr
import pandas as pd
from datetime import datetime, timezone, timedelta

BUCKET = os.environ["BUCKET_NAME"]
s3 = boto3.client("s3")

def get_target_date(event):
    if event and "date" in event:
        return datetime.strptime(event["date"], "%Y-%m-%d").date()
    return (datetime.now(timezone.utc) - timedelta(days=1)).date()

def load_silver(target_date):
    year = str(target_date.year)
    month = str(target_date.month).zfill(2)
    day = str(target_date.day).zfill(2)

    prefixes = ["jobs", "polls", "posts", "tweets", "users"]

    dfs = []
    for prefix in prefixes:
        path = f"s3://{BUCKET}/silver/{prefix}/year={year}/month={month}/day={day}/"
        try:
            df = wr.s3.read_parquet(path=path, dataset=False)
            df["_source"] = prefix
            dfs.append(df)
            print(f"  Loaded {prefix}: {len(df)} rows")
        except Exception as e:
            print(f"  Skipping {prefix}: {e}")
            continue

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)

def handler(event, context):
    print(json.dumps(event or {}))
    target_date = get_target_date(event)
    print(f"Target date: {target_date}")

    try:
        df = load_silver(target_date)
    except Exception as e:
        print(f"Failed to load silver: {e}")
        return {"statusCode": 500, "msg": str(e)}

    if df.empty:
        return {"statusCode": 200, "msg": "no data"}

    if "created_at" in df.columns:
        df["date"] = pd.to_datetime(df["created_at"], errors="coerce").dt.date
    elif "year" in df.columns:
        df["date"] = pd.to_datetime(
            df["year"] + "-" + df["month"] + "-" + df["day"], errors="coerce"
        ).dt.date
    else:
        df["date"] = target_date

    df = df[df["date"] == target_date]
    if df.empty:
        return {"statusCode": 200, "msg": "no data for date"}

    gold = f"s3://{BUCKET}/gold/"

    if "post_type" in df.columns:
        daily_posts = (
            df.groupby(["date", "post_type"])
            .size()
            .reset_index(name="count")
        )
        wr.s3.to_parquet(
            df=daily_posts,
            path=f"{gold}daily_posts/",
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=["date"]
        )
        print(f"  Wrote daily_posts: {len(daily_posts)} rows")

    if "username" in df.columns and "platform" in df.columns:
        daily_users = (
            df.groupby(["date", "platform"])
            .agg(total_users=("username", "nunique"))
            .reset_index()
        )
        wr.s3.to_parquet(
            df=daily_users,
            path=f"{gold}daily_users/",
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=["date", "platform"]
        )
        print(f"  Wrote daily_users: {len(daily_users)} rows")

    if "followers" in df.columns and "platform" in df.columns:
        x = df[df["platform"] == "X"]
        if not x.empty:
            top_x = x.sort_values("followers", ascending=False).head(10).copy()
            top_x["date"] = target_date
            wr.s3.to_parquet(
                df=top_x,
                path=f"{gold}top_x_users/",
                dataset=True,
                mode="overwrite_partitions",
                partition_cols=["date"]
            )
            print(f"  Wrote top_x_users: {len(top_x)} rows")

    if "karma_score" in df.columns and "platform" in df.columns:
        hn = df[df["platform"] == "HackerNews"]
        if not hn.empty:
            top = hn.sort_values("karma_score", ascending=False).head(10).copy()
            low = hn.sort_values("karma_score", ascending=True).head(10).copy()
            top["date"] = target_date
            low["date"] = target_date
            wr.s3.to_parquet(
                df=top,
                path=f"{gold}top_hn_users/",
                dataset=True,
                mode="overwrite_partitions",
                partition_cols=["date"]
            )
            wr.s3.to_parquet(
                df=low,
                path=f"{gold}low_hn_users/",
                dataset=True,
                mode="overwrite_partitions",
                partition_cols=["date"]
            )
            print(f"  Wrote top/low_hn_users: {len(top)} rows each")

    if "points" in df.columns and "post_type" in df.columns:
        jobs = df[df["post_type"] == "job"]
        if not jobs.empty:
            top_jobs = jobs.sort_values("points", ascending=False).head(10).copy()
            top_jobs["date"] = target_date
            wr.s3.to_parquet(
                df=top_jobs,
                path=f"{gold}top_jobs/",
                dataset=True,
                mode="overwrite_partitions",
                partition_cols=["date"]
            )
            print(f"  Wrote top_jobs: {len(top_jobs)} rows")

        posts = df[df["post_type"].isin(["story", "ask_hn", "show_hn"])]
        if not posts.empty:
            top_posts = posts.sort_values("points", ascending=False).head(10).copy()
            top_posts["date"] = target_date
            wr.s3.to_parquet(
                df=top_posts,
                path=f"{gold}top_posts/",
                dataset=True,
                mode="overwrite_partitions",
                partition_cols=["date"]
            )
            print(f"  Wrote top_posts: {len(top_posts)} rows")

    dq = float(df.notnull().mean().mean())
    dq_df = pd.DataFrame([{
        "date": target_date,
        "data_quality_score": round(dq, 4)
    }])
    wr.s3.to_parquet(
        df=dq_df,
        path=f"{gold}data_quality/",
        dataset=True,
        mode="overwrite_partitions",
        partition_cols=["date"]
    )

    print(f"Done for {target_date}, DQ score: {dq:.4f}")
    return {"statusCode": 200, "date": str(target_date)}