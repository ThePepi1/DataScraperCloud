import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone


DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()


def safe_str(value, limit=1000):
    if value is None:
        return "N/A"
    return str(value)[:limit]


def safe_json(value, limit=1000):
    try:
        return json.dumps(value, indent=2, default=str)[:limit]
    except Exception:
        return str(value)[:limit]


def now():
    return datetime.now(timezone.utc).isoformat()


def format_discord_payload(event: dict):
    detail_type = event.get("detail-type", "Unknown")
    detail = event.get("detail", {}) or {}
    source = event.get("source", "aws")
    region = event.get("region", "unknown")
    timestamp = event.get("time", now())

    if detail_type == "Lambda Function Invocation Result - Failure":
        fn_arn = detail.get("requestContext", {}).get("functionArn", "N/A")
        fn_name = fn_arn.split(":")[-1] if fn_arn else "N/A"

        error_type = detail.get("responsePayload", {}).get("errorType", "Unknown")
        error_message = detail.get("responsePayload", {}).get("errorMessage", "No message")
        request_id = detail.get("requestContext", {}).get("requestId", "N/A")

        return {
            "embeds": [{
                "title": "🚨 Lambda Failed",
                "color": 0xFF0000,
                "fields": [
                    {"name": "Function", "value": safe_str(fn_name), "inline": True},
                    {"name": "Region", "value": safe_str(region), "inline": True},
                    {"name": "Error Type", "value": safe_str(error_type), "inline": False},
                    {"name": "Error Message", "value": f"```{safe_str(error_message, 800)}```", "inline": False},
                    {"name": "Request ID", "value": safe_str(request_id), "inline": False},
                ],
                "footer": {"text": "AWS Lambda • EventBridge"},
                "timestamp": timestamp,
            }]
        }

    if source == "aws.glue" and detail_type == "Glue Job State Change":
        state = detail.get("state", "N/A")

        if state not in ("FAILED", "TIMEOUT", "ERROR"):
            return None

        return {
            "embeds": [{
                "title": f"🚨 Glue {state}",
                "color": 0xFF0000,
                "fields": [
                    {"name": "Job", "value": safe_str(detail.get("jobName")), "inline": True},
                    {"name": "State", "value": safe_str(state), "inline": True},
                    {"name": "Run ID", "value": safe_str(detail.get("jobRunId")), "inline": False},
                    {"name": "Message", "value": safe_str(detail.get("message"), 800), "inline": False},
                ],
                "footer": {"text": "AWS Glue • EventBridge"},
                "timestamp": timestamp,
            }]
        }

    if source == "aws.states" and detail_type == "Step Functions Execution Status Change":
        status = detail.get("status", "N/A")

        if status not in ("FAILED", "TIMED_OUT", "ABORTED"):
            return None

        return {
            "embeds": [{
                "title": f"🚨 Step Functions {status}",
                "color": 0xFF0000,
                "fields": [
                    {"name": "State Machine", "value": safe_str(detail.get("stateMachineArn", "").split(":")[-1]), "inline": True},
                    {"name": "Status", "value": safe_str(status), "inline": True},
                    {"name": "Execution", "value": safe_str(detail.get("executionArn", "").split(":")[-1]), "inline": False},
                    {"name": "Error", "value": safe_str(detail.get("error")), "inline": False},
                    {"name": "Cause", "value": safe_str(detail.get("cause"), 800), "inline": False},
                ],
                "footer": {"text": "AWS Step Functions • EventBridge"},
                "timestamp": timestamp,
            }]
        }

    return {
        "embeds": [{
            "title": "⚠️ AWS Event",
            "color": 0xFFA500,
            "fields": [
                {"name": "Source", "value": safe_str(source), "inline": True},
                {"name": "Detail Type", "value": safe_str(detail_type), "inline": True},
                {"name": "Region", "value": safe_str(region), "inline": True},
                {"name": "Detail", "value": f"```json\n{safe_json(detail, 800)}\n```", "inline": False},
            ],
            "footer": {"text": "EventBridge"},
            "timestamp": timestamp,
        }]
    }


def send_discord_message(payload: dict):
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL is empty")

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"  
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 204):
                raise RuntimeError(f"Discord HTTP {resp.status}")

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Discord HTTP error {e.code}: {body}") from e



def lambda_handler(event, context):
    print("EVENT:", json.dumps(event, default=str))
    print("WEBHOOK:", DISCORD_WEBHOOK_URL[:50] + "...")

    try:
        payload = format_discord_payload(event)

        if not payload:
            print("Skipped event")
            return {"statusCode": 200, "body": "SKIPPED"}

        send_discord_message(payload)

        print("Discord message sent")
        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        print("ERROR:", str(e))
        raise