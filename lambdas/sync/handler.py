import os
import json
import boto3
import awswrangler as wr
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone, timedelta

BUCKET = os.environ["BUCKET_NAME"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

GOLD_TABLES = [
    "daily_posts",
    "daily_users",
    "top_x_users",
    "top_hn_users",
    "low_hn_users",
    "top_jobs",
    "top_posts",
    "data_quality",
]


def get_target_dates(event):
    """
    Vraća listu date objekata koje treba sinhronizovati.
    - Ako event sadrži "dates" (lista "YYYY-MM-DD" stringova od gold layer-a
      preko Step Function-a), parsira i vraća tu listu.
    - Ako event sadrži pojedinačni "date" (legacy/ručni poziv), vraća listu sa jednim elementom.
    - Inače fallback: "juče" (isto ponašanje kao i ranije).
    """
    if event and "dates" in event and event["dates"]:
        return [datetime.strptime(d, "%Y-%m-%d").date() for d in event["dates"]]

    if event and "date" in event:
        return [datetime.strptime(event["date"], "%Y-%m-%d").date()]

    return [(datetime.now(timezone.utc) - timedelta(days=1)).date()]


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10
    )


def load_gold_table(table, target_date):
    path = f"s3://{BUCKET}/gold/{table}/"
    try:
        df = wr.s3.read_parquet(
            path=path,
            dataset=True,
            partition_filter=lambda x: x.get("date") == str(target_date)
        )
        print(f"  Loaded {table}: {len(df)} rows")
        return df
    except Exception as e:
        print(f"  Skipping {table}: {e}")
        return pd.DataFrame()


def df_to_postgres(conn, df, table):
    if df.empty:
        return

    # Konvertuj sve kolone u Python native tipove
    df = df.copy()
    for col in df.columns:
        df[col] = df[col].apply(lambda x: None if pd.isna(x) else (
            int(x) if isinstance(x, (int,)) else (
                float(x) if isinstance(x, float) else
                str(x)
            )))

    cols = list(df.columns)
    values = [tuple(row) for row in df.itertuples(index=False)]

    create_cols = ", ".join([f'"{c}" TEXT' for c in cols])
    insert_cols = ", ".join([f'"{c}"' for c in cols])

    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                {create_cols}
            )
        """)
        execute_values(cur, f"""
            INSERT INTO {table} ({insert_cols})
            VALUES %s
            ON CONFLICT DO NOTHING
        """, values)
    conn.commit()
    print(f"  Wrote {table}: {len(df)} rows")


def sync_single_date(conn, target_date):
    print(f"Syncing gold -> PostgreSQL for {target_date}")
    results = {}
    for table in GOLD_TABLES:
        df = load_gold_table(table, target_date)
        try:
            df_to_postgres(conn, df, table)
            results[table] = len(df)
        except Exception as e:
            print(f"  Failed {table} for {target_date}: {e}")
            results[table] = f"ERROR: {e}"
    return results


def handler(event, context):
    print(json.dumps(event or {}))
    target_dates = get_target_dates(event)
    print(f"Processing {len(target_dates)} date(s): {[str(d) for d in target_dates]}")

    try:
        conn = get_conn()
        print("  DB connected")
    except Exception as e:
        return {"statusCode": 500, "msg": f"DB connection failed: {e}"}

    all_results = {}
    for target_date in target_dates:
        all_results[str(target_date)] = sync_single_date(conn, target_date)

    conn.close()
    print(f"Done: {all_results}")
    return {
        "statusCode": 200,
        "dates": [str(d) for d in target_dates],
        "results": all_results,
    }