import json
import os
from datetime import datetime, timezone, timedelta
import requests

BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"


def get_yesterday():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    start = yesterday.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    ).timestamp()

    end = yesterday.replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=0
    ).timestamp()

    return int(start), int(end), yesterday.strftime("%Y/%m/%d")


def save_locally(data, item_type, date_path, page):
    folder = f"local_data/bronze/hackernews/{date_path}/{item_type}"

    os.makedirs(folder, exist_ok=True)

    file_path = f"{folder}/page_{page}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(data)} items to {file_path}")


def fetch_and_save_items(tag, start, end, date_path):
    page = 0
    total_saved = 0

    while True:
        print(f"Fetching {tag} page {page}...")

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
            print(f"No more {tag} results.")
            break

        save_locally(hits, tag, date_path, page)

        total_saved += len(hits)

        if page >= data.get("nbPages", 1) - 1:
            break

        page += 1

    return total_saved


def main():
    start, end, date_path = get_yesterday()

    types = [
        "story",
        "ask_hn",
        "show_hn",
        "job",
        "poll",
        "comment"
    ]

    result = {}

    for item_type in types:
        print(f"\n=== Processing {item_type} ===")

        saved_count = fetch_and_save_items(
            item_type,
            start,
            end,
            date_path
        )

        result[item_type] = saved_count

    print("\nDONE")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()