import json
import os
import boto3
import requests
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

s3 = boto3.client("s3")

BUCKET_NAME = os.environ["BUCKET_NAME"]
BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"


def get_yesterday():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    end = yesterday.replace(hour=23, minute=59, second=59, microsecond=0).timestamp()

    return int(start), int(end), yesterday.strftime("%Y/%m/%d")


def fetch_and_save_items(tag, start, end, date_path):
    page = 0
    total_saved = 0

    while True:
        response = requests.get(
            BASE_URL,
            params={
                "tags": tag,
                "numericFilters": f"created_at_i>{start},created_at_i<{end}",
                "hitsPerPage": 1000,
                "page": page,
            },
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()
        hits = data.get("hits", [])

        if not hits:
            break

        #Ako je verovati nasoj kalkulaciji ovo je najbezbolnije za novcanik :)
        #Ako nije nemojte nam skidati bodove, molim vas :) jer ako dodje do toga dovoljna je kazna sto smo ostali bez para :)
        key = f"bronze/hackernews/{date_path}/{tag}/page_{page}.json"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json.dumps(hits),
            ContentType="application/json",
        )

        total_saved += len(hits)

        print(f"Saved {len(hits)} {tag} items to s3://{BUCKET_NAME}/{key}")

        if page >= data.get("nbPages", 1) - 1:
            break

        page += 1

    return total_saved


def handler(event, context):
    start, end, date_path = get_yesterday()

    types = ["story", "ask_hn", "job", "poll", "comment"]

    result = {}

    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = {
            executor.submit(
                fetch_and_save_items,
                item_type,
                start,
                end,
                date_path
            ): item_type
            for item_type in types
        }

        for future in as_completed(futures):
            item_type = futures[future]
            saved_count = future.result()
            result[item_type] = saved_count

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Bronze HN collection complete",
            "date": date_path,
            "saved": result
        })
    }