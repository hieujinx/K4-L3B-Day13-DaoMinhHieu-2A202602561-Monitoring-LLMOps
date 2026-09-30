from __future__ import annotations

import html
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
OUTPUT_PATH = REPO_ROOT / "submission" / "evidence" / "dashboard.html"


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def load_records() -> list[dict]:
    if not LOG_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy {LOG_PATH}; hãy chạy load_test.py trước.")
    return [
        json.loads(line)
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_dashboard(records: list[dict]) -> str:
    timestamps = [
        datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        for record in records
        if record.get("ts")
    ]
    window_end = max(timestamps, default=datetime.now(timezone.utc))
    cutoff = window_end - timedelta(minutes=60)
    recent = [
        record
        for record in records
        if datetime.fromisoformat(record["ts"].replace("Z", "+00:00")) >= cutoff
    ]
    responses = [r for r in recent if r.get("event") == "response_sent"]
    requests = [r for r in recent if r.get("event") == "request_received"]
    failures = [r for r in recent if r.get("event") == "request_failed"]
    tool_events = [r for r in recent if "tool_success" in r]
    latency = [float(r["latency_ms"]) for r in responses]
    ttft = [float(r["ttft_ms"]) for r in responses]
    costs = [float(r["cost_usd"]) for r in responses]
    tokens_in = sum(int(r["tokens_in"]) for r in responses)
    tokens_out = sum(int(r["tokens_out"]) for r in responses)
    quality = [float(r["quality_score"]) for r in responses]
    success_rate = (
        sum(bool(r["tool_success"]) for r in tool_events) / len(tool_events) * 100
        if tool_events
        else 0
    )
    error_rate = len(failures) / len(requests) * 100 if requests else 0
    panels = [
        ("Latency", f"P50 {percentile(latency, 50):.0f} ms | P95 {percentile(latency, 95):.0f} ms | P99 {percentile(latency, 99):.0f} ms | TTFT P95 {percentile(ttft, 95):.0f} ms", "Threshold: P95 <= 3000 ms"),
        ("Traffic", f"{len(requests)} requests | {len(requests) / 60:.2f} requests/min", "Threshold: >= 1 request/min"),
        ("Errors", f"Error rate {error_rate:.2f}% | Retrieval success {success_rate:.2f}%", "Threshold: error <= 2%; retrieval >= 90%"),
        ("Cost", f"Total ${sum(costs):.6f}", "Threshold: total <= $2.50"),
        ("Tokens", f"Input {tokens_in} | Output {tokens_out} | Total {tokens_in + tokens_out}", "Threshold: total <= 50000"),
        ("Quality", f"Mean score {sum(quality) / len(quality):.2f}" if quality else "Mean score 0.00", "Threshold: mean >= 0.75"),
    ]
    cards = "\n".join(
        f'<section class="card"><h2>{html.escape(title)}</h2><p>{html.escape(value)}</p><small>{html.escape(threshold)}</small></section>'
        for title, value, threshold in panels
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="30">
<title>K4-L3B Monitoring Dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #101827; color: #e5e7eb; }}
.grid {{ display: grid; grid-template-columns: repeat(3, minmax(220px, 1fr)); gap: 1rem; }}
.card {{ background: #1f2937; border: 1px solid #4b5563; border-radius: 10px; padding: 1rem; min-height: 120px; }}
h1 {{ margin-bottom: .25rem; }} h2 {{ color: #93c5fd; margin-top: 0; }} p {{ font-size: 1.1rem; }}
small {{ color: #fbbf24; }} .meta {{ color: #9ca3af; margin-bottom: 1.5rem; }}
</style>
</head>
<body>
<h1>K4-L3B Day 13 Monitoring &amp; LLMOps</h1>
<div class="meta">Time range: last 60 minutes | Refresh: 30 seconds | Source: data/logs.jsonl (UTC)</div>
<main class="grid">{cards}</main>
</body>
</html>"""


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_dashboard(load_records()), encoding="utf-8")
    print(f"Dashboard created: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
