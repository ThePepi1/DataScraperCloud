import boto3
import json
from datetime import datetime, timedelta

lambda_client = boto3.client("lambda", region_name="eu-central-1")
LAMBDA_NAME = "gold_lambda"

def run_date(date_str):
    print(f"  Invoking lambda for {date_str}...", end=" ", flush=True)
    response = lambda_client.invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps({"date": date_str})
    )
    result = json.loads(response["Payload"].read())
    status = result.get("statusCode", "?")
    msg = result.get("msg", "")
    
    if status == 200:
        print(f"OK {f'({msg})' if msg else ''}")
    else:
        print(f"FAILED — {result}")
    
    return status == 200

def backfill(start_date: str, end_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    if start > end:
        print("Greška: start_date mora biti prije end_date")
        return
    
    total = (end - start).days + 1
    print(f"\nBackfill: {start_date} → {end_date} ({total} dana)\n")
    
    success, failed, skipped = [], [], []
    
    current = start
    while current <= end:
        date_str = str(current)
        try:
            ok = run_date(date_str)
            if ok:
                success.append(date_str)
            else:
                failed.append(date_str)
        except Exception as e:
            print(f"  EXCEPTION — {e}")
            failed.append(date_str)
        current += timedelta(days=1)
    
    print(f"\n{'='*40}")
    print(f"Rezultati:")
    print(f"  Uspjesno:  {len(success)}/{total}")
    print(f"  Failovi:   {len(failed)}/{total}")
    if failed:
        print(f"\n  Failed datumi:")
        for d in failed:
            print(f"    - {d}")
    print(f"{'='*40}\n")

if __name__ == "__main__":
    print("Gold Layer Backfill")
    print("===================")
    start = input("Start date (YYYY-MM-DD): ").strip()
    end = input("End date   (YYYY-MM-DD): ").strip()
    
    try:
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        print("Greška: neispravan format datuma, koristi YYYY-MM-DD")
        exit(1)
    
    confirm = input(f"\nPokreni backfill od {start} do {end}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Otkazano.")
        exit(0)
    
    backfill(start, end)