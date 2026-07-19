import asyncio
import csv
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx
import redis

load_dotenv()

API_URL = "http://127.0.0.1:8000/ask"
QUERIES_PATH = Path(__file__).parent / "queries.csv"
RESULTS_DIR = Path(__file__).parent / "results"


def clear_upstash_cache():
    try:
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise ValueError("Missing REDIS_URL environment variable.")
        client = redis.Redis.from_url(redis_url, decode_responses=True)  # no ssl= kwarg
        result = client.flushdb()
        print("Cache cleared successfully.\n" if result else "Failed to clear cache.\n")
    except Exception as e:
        print(f"Error clearing cache: {e}\n")

def str2bool(value: str):
    """CSV fields arrive as strings ('True'/'False'/''). An empty field means
    'not applicable - don't check this field' and must stay None, not collapse
    to False, or it'll get compared against real values on rows where that
    field was never meant to be checked."""
    v = str(value).strip().lower()
    if v == "":
        return None
    return v in ("true", "1", "yes")


def parse_expected(row: dict) -> dict:
    return {
        "status_code": int(row["expected_status_code"]) if row["expected_status_code"] else None,
        "pii_detected": str2bool(row["expected_pii_detected"]),
        "injection_flagged": str2bool(row["expected_injection_flagged"]),
        "cache_hit": str2bool(row["expected_cache_hit"]),
    }


def check_field(label: str, expected, actual, note: str) -> bool:
    """Returns True if this field passes (or wasn't checked). Prints result."""
    if expected is None:
        return True
    if expected == actual:
        print(f"  \u2705 {label} matched - {actual}")
        return True
    print(f"  \u274c {label} mismatch: expected {expected}, got {actual}\n     Note: {note}")
    return False


async def run_one(client: httpx.AsyncClient, row: dict) -> dict:
    query = row["query"]
    category = row["category"]
    note = row["notes"]
    expected = parse_expected(row)

    base_result = {
        "id": row["id"],
        "category": category,
        "query": query,
        "expected": expected,
    }

    try:
        resp = await client.post(
            API_URL,
            json={"query": query, "user_id": "anonymous", "provider": "openai"},
            timeout=60.0,
        )
        actual_status_code = resp.status_code
        data = resp.json()
    except Exception as e:
        return {**base_result, "passed": False, "error": f"request failed: {e}"}

    checks = []

    # Status code always applies, regardless of category, and always
    # comes straight from the HTTP response, never from the body.
    checks.append(check_field("status_code", expected["status_code"], actual_status_code, note))

    # Everything below this line only exists in a real 200 response body.
    # Error responses ({"detail": "..."}) have none of these fields, so
    # skip body-shape checks entirely when the call was rejected.
    if actual_status_code == 200:
        # Success shape is CacheEntry: {"response": {...AskResponse}, "cached_at": ...}
        ask_response = data.get("response", {})
        actual_pii = ask_response.get("pii_detected")
        actual_cache_hit = ask_response.get("cache_hit")

        checks.append(check_field("pii_detected", expected["pii_detected"], actual_pii, note))
        checks.append(check_field("cache_hit", expected["cache_hit"], actual_cache_hit, note))

        if expected["cache_hit"]:
            if data.get("cached_at") is None:
                print(f"  \u274c expected cached_at to be set on a cache hit, got None\n     Note: {note}")
                checks.append(False)
            else:
                checks.append(True)

    else:
        # Rejected request (403 injection, 400 token limit, 422 validation, 429 rate limit).
        # Only meaningful check left is the detail message existing at all.
        if "detail" not in data:
            print(f"  \u274c expected an error 'detail' field in a {actual_status_code} response, got: {data}")
            checks.append(False)

    passed = all(checks)
    return {**base_result, "passed": passed, "actual_status_code": actual_status_code}


async def main():
    clear_upstash_cache()

    with open(QUERIES_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    async with httpx.AsyncClient() as client:
        for row in rows:
            print(f'[{row["id"]}] {row["category"]}: {row["query"][:60]!r}')
            result = await run_one(client, row)
            print(f'  --> {"PASSED" if result["passed"] else "FAILED"}\n')
            results.append(result)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "eval_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n{passed}/{total} passed.")

    failed = [r for r in results if not r["passed"]]
    if failed:
        print("\nFailed cases:")
        for r in failed:
            print(f"  [{r['id']}] {r['category']}: {r['query'][:60]!r}")

    print(f"\nFull results written to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())