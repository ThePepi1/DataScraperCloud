import json
import os
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"


def get_yesterday():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    end = yesterday.replace(hour=23, minute=59, second=59, microsecond=0).timestamp()
    return int(start), int(end), yesterday.strftime("%Y/%m/%d")


def get_time_chunks(start, end, chunk_hours=2):
    chunks = []
    chunk_size = chunk_hours * 3600
    current = start
    while current < end:
        chunk_end = min(current + chunk_size, end)
        chunks.append((current, chunk_end))
        current = chunk_end
    return chunks


def save_locally(data, item_type, date_path, chunk_index, page):
    folder = f"local_data/bronze/hackernews/{date_path}/{item_type}"
    os.makedirs(folder, exist_ok=True)
    file_path = f"{folder}/chunk_{chunk_index}_page_{page}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_chunk(tag, chunk_start, chunk_end, date_path, chunk_index):
    page = 0
    total_saved = 0
    while True:
        response = requests.get(
            BASE_URL,
            params={
                "tags": tag,
                "numericFilters": f"created_at_i>{chunk_start},created_at_i<{chunk_end}",
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

        save_locally(hits, tag, date_path, chunk_index, page)
        total_saved += len(hits)

        nb_pages = data.get("nbPages", 1)

        if page >= nb_pages - 1:
            break
        page += 1

    return total_saved


def fetch_and_save_items(tag, start, end, date_path, chunk_hours=2):
    chunks = get_time_chunks(start, end, chunk_hours)
    total_saved = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fetch_chunk, tag, chunk_start, chunk_end, date_path, i): i
            for i, (chunk_start, chunk_end) in enumerate(chunks)
        }
        for future in as_completed(futures):
            total_saved += future.result()

    return total_saved


def main():
    start, end, date_path = get_yesterday()
    types = ["story", "ask_hn", "show_hn", "job", "poll", "comment"]
    result = {}

    for item_type in types:
        result[item_type] = fetch_and_save_items(item_type, start, end, date_path)



if __name__ == "__main__":
    main()