import os
import json
import boto3
import awswrangler as wr
import pandas as pd
from datetime import datetime, timezone, timedelta

BUCKET = os.environ["BUCKET_NAME"]
s3 = boto3.client("s3")


def get_target_dates(event):
    """
    Vraća listu date objekata koje treba obraditi.
    - Ako event sadrži "dates" (lista "YYYY-MM-DD" stringova od normalize_hn
      preko Step Function-a), parsira i vraća tu listu.
    - Ako event sadrži pojedinačni "date" (legacy/ručni poziv), vraća listu sa jednim elementom.
    - Inače fallback: "juče" (isto ponašanje kao i ranije).
    """
    if event and "dates" in event and event["dates"]:
        return [datetime.strptime(d, "%Y-%m-%d").date() for d in event["dates"]]

    if event and "date" in event:
        return [datetime.strptime(event["date"], "%Y-%m-%d").date()]

    return [(datetime.now(timezone.utc) - timedelta(days=1)).date()]


def load_silver(target_date):
    year = str(target_date.year)
    month = str(target_date.month).zfill(2)
    day = str(target_date.day).zfill(2)

    prefixes = ["jobs", "polls", "posts", "tweets"]

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

    try:
        df_users = wr.s3.read_parquet(
            path=f"s3://{BUCKET}/silver/users/",
            dataset=True,
            filters=[("platform", "=", "HackerNews")],
            boto3_session=boto3.Session(),
        )
        df_users["_source"] = "users"
        dfs.append(df_users)
        print(f"  Loaded users: {len(df_users)} rows")
    except Exception as e:
        print(f"  Skipping users: {e}")

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)


def process_single_date(target_date):
    """
    Radi celu gold agregaciju za jedan dan. Vraća True ako je bilo
    podataka i nešto je upisano, False ako je dan bio prazan.
    """
    print(f"Target date: {target_date}")

    try:
        df = load_silver(target_date)
    except Exception as e:
        print(f"Failed to load silver for {target_date}: {e}")
        return False

    if df.empty:
        print(f"  No data for {target_date}")
        return False

    if "created_at" in df.columns:
        df["date"] = pd.to_datetime(df["created_at"], errors="coerce").dt.date
    elif "year" in df.columns:
        df["date"] = pd.to_datetime(
            df["year"] + "-" + df["month"] + "-" + df["day"], errors="coerce"
        ).dt.date
    else:
        df["date"] = target_date

    gold = f"s3://{BUCKET}/gold/"
    wrote_anything = False

    # --- daily_posts ---
    # HN: story, ask_hn, show_hn, job, poll, comment
    # X:  tweet, retweet
    daily_parts = []

    if "post_type" in df.columns:
        hn_posts = df[
            (df["_source"].isin(["posts", "jobs", "polls"])) &
            (df["date"] == target_date)
        ]
        if not hn_posts.empty:
            hn_counts = (
                hn_posts.groupby(["date", "post_type"])
                .size()
                .reset_index(name="count")
            )
            daily_parts.append(hn_counts)

        x_posts = df[
            (df["_source"] == "tweets") &
            (df["date"] == target_date)
        ]
        if not x_posts.empty:
            x_counts = (
                x_posts.groupby(["date", "post_type"])
                .size()
                .reset_index(name="count")
            )
            daily_parts.append(x_counts)

    if daily_parts:
        daily_posts = pd.concat(daily_parts, ignore_index=True)
        wr.s3.to_parquet(
            df=daily_posts,
            path=f"{gold}daily_posts/",
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=["date"],
        )
        print(f"  Wrote daily_posts: {len(daily_posts)} rows")
        wrote_anything = True

    posts_df = df[df["_source"].isin(["posts", "jobs", "polls"]) & (df["date"] == target_date)]
    tweets_df = df[df["_source"] == "tweets"]

    # --- daily_users HackerNews ---
    if not posts_df.empty and "author_username" in posts_df.columns:
        hn_user_count = posts_df["author_username"].nunique()
        daily_users_hn = pd.DataFrame([{
            "date": target_date,
            "platform": "HackerNews",
            "total_users": hn_user_count,
        }])
        wr.s3.to_parquet(
            df=daily_users_hn,
            path=f"{gold}daily_users/",
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=["date", "platform"],
        )
        print(f"  Wrote daily_users HackerNews: {hn_user_count} unique users")
        wrote_anything = True

    # --- daily_users X ---
    if not tweets_df.empty:
        tweets_date_df = tweets_df[tweets_df["date"] == target_date]
        if not tweets_date_df.empty and "author_username" in tweets_date_df.columns:
            x_user_count = tweets_date_df["author_username"].nunique()
            daily_users_x = pd.DataFrame([{
                "date": target_date,
                "platform": "X",
                "total_users": x_user_count,
            }])
            wr.s3.to_parquet(
                df=daily_users_x,
                path=f"{gold}daily_users/",
                dataset=True,
                mode="overwrite_partitions",
                partition_cols=["date", "platform"],
            )
            print(f"  Wrote daily_users X: {x_user_count} unique users")
            wrote_anything = True

    # --- top_x_users (top 10 po followers, particionirano po danu) ---
    if not tweets_df.empty and "followers" in tweets_df.columns:
        tweets_date_df = tweets_df[tweets_df["date"] == target_date]
        if not tweets_date_df.empty:
            top_x = (
                tweets_date_df.groupby("author_username")["followers"]
                .max()
                .reset_index()
                .sort_values("followers", ascending=False)
                .head(10)
                .copy()
            )
            top_x.columns = ["username", "followers"]
            top_x["date"] = target_date
            wr.s3.to_parquet(
                df=top_x,
                path=f"{gold}top_x_users/",
                dataset=True,
                mode="overwrite_partitions",
                partition_cols=["date"],
            )
            print(f"  Wrote top_x_users: {len(top_x)} rows")
            wrote_anything = True

    # --- top/low HN users ---
    if not posts_df.empty and "author_username" in posts_df.columns:

        agg_dict = {"post_count": ("author_username", "count")}
        if "karma_score" in posts_df.columns:
            agg_dict["karma_score"] = ("karma_score", "max")

        user_activity = (
            posts_df.groupby("author_username")
            .agg(**agg_dict)
            .reset_index()
        )

        if "karma_score" not in user_activity.columns:
            user_activity["karma_score"] = None

        user_activity["date"] = target_date
        user_activity["platform"] = "HackerNews"

        users_df = df[df["_source"] == "users"]
        if not users_df.empty and "username" in users_df.columns and "karma_score" in users_df.columns:
            karma_map = (
                users_df[["username", "karma_score"]]
                .dropna(subset=["karma_score"])
                .drop_duplicates(subset=["username"])
            )
            if not karma_map.empty:
                user_activity = user_activity.drop(columns=["karma_score"], errors="ignore")
                user_activity = user_activity.merge(
                    karma_map.rename(columns={"username": "author_username"}),
                    on="author_username",
                    how="left",
                )

        sort_cols = []
        if "karma_score" in user_activity.columns and user_activity["karma_score"].notna().any():
            sort_cols.append("karma_score")
        sort_cols.append("post_count")

        top_hn = user_activity.sort_values(sort_cols, ascending=False).head(10).copy()
        low_hn = user_activity.sort_values(sort_cols, ascending=True).head(10).copy()

        wr.s3.to_parquet(
            df=top_hn,
            path=f"{gold}top_hn_users/",
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=["date"],
        )
        wr.s3.to_parquet(
            df=low_hn,
            path=f"{gold}low_hn_users/",
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=["date"],
        )
        print(f"  Wrote top/low_hn_users: {len(top_hn)} rows each")
        wrote_anything = True

    # --- top_jobs ---
    jobs_df = df[(df["_source"] == "jobs") & (df["date"] == target_date)]
    if not jobs_df.empty and "points" in jobs_df.columns:
        top_jobs = jobs_df.sort_values("points", ascending=False).head(10).copy()
        top_jobs["date"] = target_date
        wr.s3.to_parquet(
            df=top_jobs,
            path=f"{gold}top_jobs/",
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=["date"],
        )
        print(f"  Wrote top_jobs: {len(top_jobs)} rows")
        wrote_anything = True

    # --- top_posts ---
    if "post_type" in df.columns and "points" in df.columns:
        story_df = df[
            (df["post_type"].isin(["story", "ask_hn", "show_hn"])) &
            (df["date"] == target_date)
        ]
        if not story_df.empty:
            top_posts = story_df.sort_values("points", ascending=False).head(10).copy()
            top_posts["date"] = target_date
            wr.s3.to_parquet(
                df=top_posts,
                path=f"{gold}top_posts/",
                dataset=True,
                mode="overwrite_partitions",
                partition_cols=["date"],
            )
            print(f"  Wrote top_posts: {len(top_posts)} rows")
            wrote_anything = True

    # --- data_quality ---
    dq_df_source = df[df["date"] == target_date] if "date" in df.columns else df
    if not dq_df_source.empty:
        dq = float(dq_df_source.notnull().mean().mean())
        dq_row = pd.DataFrame([{
            "date": target_date,
            "data_quality_score": round(dq, 4),
        }])
        wr.s3.to_parquet(
            df=dq_row,
            path=f"{gold}data_quality/",
            dataset=True,
            mode="overwrite_partitions",
            partition_cols=["date"],
        )
        print(f"  Wrote data_quality, DQ score: {dq:.4f}")
        wrote_anything = True

    print(f"Done for {target_date}")
    return wrote_anything


def handler(event, context):
    print(json.dumps(event or {}))
    target_dates = get_target_dates(event)
    print(f"Processing {len(target_dates)} date(s): {[str(d) for d in target_dates]}")

    processed_dates = []
    for target_date in target_dates:
        try:
            had_data = process_single_date(target_date)
            if had_data:
                processed_dates.append(str(target_date))
        except Exception as e:
            print(f"  Failed processing {target_date}: {e}")
            continue


    return {
        "statusCode": 200,
        "dates": processed_dates,
    }