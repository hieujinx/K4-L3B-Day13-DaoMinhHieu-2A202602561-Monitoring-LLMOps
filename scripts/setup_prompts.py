from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from langfuse import get_client


BASELINE_TEMPLATE = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
CANDIDATE_TEMPLATE = (
    "Feature={{feature}}\n"
    "Relevant docs:\n{{docs}}\n"
    "Question={{message}}\n"
    "Answer concisely and ground the answer in the relevant docs."
)


def _get_version(client, name: str, version: int):
    try:
        return client.get_prompt(
            name,
            version=version,
            type="text",
            cache_ttl_seconds=0,
            max_retries=0,
        )
    except Exception:
        return None


def ensure_versions(client, name: str) -> tuple[int, int]:
    baseline = _get_version(client, name, 1)
    if baseline is None:
        baseline = client.create_prompt(
            name=name,
            prompt=BASELINE_TEMPLATE,
            labels=["baseline", "production"],
            type="text",
            commit_message="Day 13 baseline prompt",
        )

    candidate = _get_version(client, name, 2)
    if candidate is None:
        candidate = client.create_prompt(
            name=name,
            prompt=CANDIDATE_TEMPLATE,
            labels=["candidate"],
            type="text",
            commit_message="Day 13 candidate prompt",
        )

    return int(baseline.version), int(candidate.version)


def set_labels(client, name: str, version: int, labels: list[str]) -> None:
    client.api.prompt_version.update(name, version, new_labels=labels)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the Day 13 prompt versions and demonstrate promote/rollback."
    )
    parser.add_argument(
        "--leave-promoted",
        action="store_true",
        help="Leave production on the candidate instead of rolling back to baseline.",
    )
    args = parser.parse_args()

    load_dotenv()
    name = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    client = get_client()
    baseline_version, candidate_version = ensure_versions(client, name)

    set_labels(client, name, baseline_version, ["baseline"])
    set_labels(client, name, candidate_version, ["candidate", "production"])
    print(
        f"PROMOTE name={name} production=v{candidate_version} "
        f"baseline=v{baseline_version} candidate=v{candidate_version}"
    )

    if not args.leave_promoted:
        set_labels(client, name, candidate_version, ["candidate"])
        set_labels(client, name, baseline_version, ["baseline", "production"])
        print(
            f"ROLLBACK name={name} production=v{baseline_version} "
            f"baseline=v{baseline_version} candidate=v{candidate_version}"
        )


if __name__ == "__main__":
    main()
