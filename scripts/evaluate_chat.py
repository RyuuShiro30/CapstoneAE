"""Measure local chatbot behavior against the synthetic foundation cases."""

import argparse
import asyncio
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from time import perf_counter

import httpx

from app.main import create_app

DEFAULT_CASES = (
    Path(__file__).resolve().parents[1]
    / "evaluations"
    / "datasets"
    / "foundation_cases.csv"
)


async def evaluate_cases(path: Path) -> dict[str, object]:
    """Call the ASGI endpoint without sending messages to external services."""
    latencies: list[float] = []
    totals: Counter[str] = Counter()
    passed: Counter[str] = Counter()
    failures: list[str] = []
    transport = httpx.ASGITransport(app=create_app(), raise_app_exceptions=False)

    with path.open(encoding="utf-8-sig", newline="") as stream:
        cases = csv.DictReader(stream)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://local"
        ) as client:
            for case in cases:
                category = case["category"]
                totals[category] += 1
                start = perf_counter()
                response = await client.post(
                    "/api/v1/chat",
                    json={
                        "session_id": "foundation-evaluation",
                        "message": case["message"],
                    },
                )
                latencies.append((perf_counter() - start) * 1000)
                if response.status_code != 200 or not response.headers.get(
                    "content-type", ""
                ).startswith("application/json"):
                    failures.append(case["id"])
                    continue
                payload = response.json()
                reply = payload.get("reply")
                handoff = {"true": True, "false": False}[case["redirect_whatsapp"]]
                if (
                    payload.get("status") == "success"
                    and payload.get("intent") == case["intent"]
                    and payload.get("redirect_whatsapp") is handoff
                    and isinstance(reply, str)
                    and case["reply_contains"].casefold() in reply.casefold()
                ):
                    passed[category] += 1
                else:
                    failures.append(case["id"])
    if not latencies:
        raise ValueError("Provide at least one evaluation case.")
    return {
        "cases": {
            category: {"passed": passed[category], "total": count}
            for category, count in sorted(totals.items())
        },
        "failed_case_ids": failures,
        "local_latency_ms": {
            "median": round(median(latencies), 3),
            "max": round(max(latencies), 3),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    report = asyncio.run(evaluate_cases(args.cases))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(report["failed_case_ids"]))


if __name__ == "__main__":
    raise SystemExit(main())
