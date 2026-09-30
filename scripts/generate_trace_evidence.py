from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _trace_ids(client, session_id: str) -> list[str]:
    result = client.api.observations.get_many(
        session_id=session_id,
        is_root_observation=True,
        limit=20,
    )
    return list(dict.fromkeys(str(observation.trace_id) for observation in result.data))


def _print_trace_summary(client, label: str, trace_id: str) -> None:
    result = client.api.observations.get_many(
        trace_id=trace_id,
        fields="core,basic,metadata,model,usage,prompt,metrics,trace_context",
        expand_metadata=(
            "correlation_id,prompt_name,prompt_label,prompt_version,"
            "prompt_source,input_tokens,output_tokens,cost_usd"
        ),
        limit=20,
    )
    print(f"TRACE_SUMMARY label={label} trace_id={trace_id}")
    for observation in sorted(result.data, key=lambda item: item.start_time):
        metadata = observation.metadata if isinstance(observation.metadata, dict) else {}
        print(
            "  "
            f"name={observation.name} type={observation.type} "
            f"parent={observation.parent_observation_id or '-'} "
            f"prompt={observation.prompt_name or metadata.get('prompt_name', '-')} "
            f"prompt_version={observation.prompt_version or metadata.get('prompt_version', '-')} "
            f"prompt_label={metadata.get('prompt_label', '-')} "
            f"correlation_id={metadata.get('correlation_id', '-')} "
            f"model={observation.model or '-'} latency_s={observation.latency or 0} "
            f"total_cost={observation.total_cost or 0}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and query Day 13 trace evidence.")
    parser.add_argument(
        "--query-only",
        action="store_true",
        help="Only query trace IDs already ingested for the evidence sessions.",
    )
    parser.add_argument(
        "--session-id",
        help="Query and summarize traces for one existing Langfuse session, then exit.",
    )
    args = parser.parse_args()
    load_dotenv()

    # Import only after .env is loaded so the Langfuse client is initialized with
    # the student's project credentials.
    from app.main import app
    from app.tracing import get_langfuse_client

    client = get_langfuse_client()
    if args.session_id:
        trace_ids = _trace_ids(client, args.session_id)
        print(f"SESSION_ID={args.session_id}")
        print(f"TRACE_IDS={','.join(trace_ids)}")
        if trace_ids:
            _print_trace_summary(client, args.session_id, trace_ids[0])
        return

    workloads = (
        ("baseline", "day13-evidence-baseline", "b1"),
        ("candidate", "day13-evidence-candidate", "c2"),
    )
    if not args.query_only:
        with TestClient(app) as http:
            for label, session_id, prefix in workloads:
                os.environ["LANGFUSE_PROMPT_LABEL"] = label
                for index in range(5):
                    correlation_id = f"req-{prefix}{index:06x}"
                    response = http.post(
                        "/chat",
                        headers={"x-request-id": correlation_id},
                        json={
                            "user_id": "lab-user-001",
                            "session_id": session_id,
                            "feature": "monitoring",
                            "message": "How do metrics, logs, and traces help find a root cause?",
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    print(
                        f"TRACE_REQUEST label={label} correlation_id={payload['correlation_id']} "
                        f"latency_ms={payload['latency_ms']}"
                    )
        client.flush()
    # The public ingestion endpoint is asynchronous. A short bounded retry lets
    # the evidence query see the traces without hiding failures indefinitely.
    for attempt in range(6):
        baseline_ids = _trace_ids(client, "day13-evidence-baseline")
        candidate_ids = _trace_ids(client, "day13-evidence-candidate")
        if len(baseline_ids) >= 5 and len(candidate_ids) >= 5:
            break
        time.sleep(2)

    print(f"BASELINE_TRACE_IDS={','.join(baseline_ids)}")
    print(f"CANDIDATE_TRACE_IDS={','.join(candidate_ids)}")
    print(f"TOTAL_EVIDENCE_TRACES={len(baseline_ids) + len(candidate_ids)}")
    if baseline_ids:
        _print_trace_summary(client, "baseline", baseline_ids[0])
    if candidate_ids:
        _print_trace_summary(client, "candidate", candidate_ids[0])


if __name__ == "__main__":
    main()
