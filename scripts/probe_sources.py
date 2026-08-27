"""Small, explicit metadata probes for Phase 0B data feasibility.

The script reads only bounded metadata responses. It does not crawl, download
datasets, follow undocumented application calls, or accept credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

FEASIBILITY_STATUSES = {
    "READY",
    "PARTIAL",
    "BLOCKED",
    "REFERENCE_ONLY",
    "NOT_NEEDED",
    "UNKNOWN",
}
HTTP_SUCCESS_MIN = 200
HTTP_REDIRECT_MIN = 300

REQUIRED_MANIFEST_FIELDS = {
    "dataset_id",
    "title",
    "provider",
    "source_url_or_id",
    "publication_date",
    "consulted_date",
    "version",
    "license",
    "attribution",
    "access_method",
    "format",
    "crs",
    "temporal_coverage",
    "spatial_coverage",
    "update_frequency",
    "authentication",
    "fields",
    "limitations",
    "nature",
    "transformation",
    "created_by_script",
    "verification_status",
    "feasibility_status",
    "supports_assumptions",
    "supports_research_questions",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_manifest(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict) or not isinstance(document.get("datasets"), list):
        return ["manifest must be an object containing a datasets list"]

    seen: set[str] = set()
    for index, dataset in enumerate(document["datasets"]):
        prefix = f"datasets[{index}]"
        if not isinstance(dataset, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = sorted(REQUIRED_MANIFEST_FIELDS - dataset.keys())
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(missing)}")
        dataset_id = dataset.get("dataset_id")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            errors.append(f"{prefix}.dataset_id must be a non-empty string")
        elif dataset_id in seen:
            errors.append(f"duplicate dataset_id: {dataset_id}")
        else:
            seen.add(dataset_id)
        if not str(dataset.get("source_url_or_id", "")).strip():
            errors.append(f"{prefix}.source_url_or_id must not be empty")
        status = dataset.get("feasibility_status")
        if status not in FEASIBILITY_STATUSES:
            errors.append(f"{prefix}.feasibility_status is invalid: {status}")
    return errors


def _summarise_body(body: bytes, content_type: str) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    stripped = body.lstrip()
    if "json" in content_type.lower() or stripped.startswith((b"{", b"[")):
        parsed = json.loads(body.decode("utf-8"))
        if isinstance(parsed, dict):
            summary["top_level_keys"] = sorted(parsed)[:30]
            layers = parsed.get("layers")
            if isinstance(layers, list):
                summary["layers"] = [
                    {"id": item.get("id"), "name": item.get("name")}
                    for item in layers[:30]
                    if isinstance(item, dict)
                ]
            fields = parsed.get("fields")
            if isinstance(fields, list):
                summary["fields"] = [
                    item.get("name") for item in fields[:100] if isinstance(item, dict)
                ]
    return summary


def fetch_probe(
    spec: dict[str, Any],
    *,
    timeout_seconds: float = 15.0,
    retries: int = 1,
    opener: Any = urllib.request.urlopen,
) -> dict[str, Any]:
    max_bytes = int(spec.get("max_bytes", 1_000_000))
    request = urllib.request.Request(
        spec["url"],
        headers={
            "Accept": spec.get(
                "accept",
                "application/json, application/xml;q=0.9, text/html;q=0.8",
            ),
            "User-Agent": "FIRSTLOOK-MAD-Phase-0B/0.1 (+research metadata probe)",
        },
        method="GET",
    )
    last_error = "UNKNOWN"
    for attempt in range(retries + 1):
        try:
            with opener(request, timeout=timeout_seconds) as response:
                body = response.read(max_bytes + 1)
                truncated = len(body) > max_bytes
                body = body[:max_bytes]
                content_type = response.headers.get("Content-Type", "UNKNOWN")
                result: dict[str, Any] = {
                    "probe_id": spec["probe_id"],
                    "url": spec["url"],
                    "ok": HTTP_SUCCESS_MIN <= response.status < HTTP_REDIRECT_MIN,
                    "http_status": response.status,
                    "content_type": content_type,
                    "bytes_read": len(body),
                    "truncated": truncated,
                    "sha256": hashlib.sha256(body).hexdigest(),
                }
                try:
                    result["body_summary"] = _summarise_body(body, content_type)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    result["body_summary_error"] = type(exc).__name__
                return result
        except OSError as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
    return {
        "probe_id": spec["probe_id"],
        "url": spec["url"],
        "ok": False,
        "error": last_error,
    }


def run_probes(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "generated_at": config["consulted_at"],
        "purpose": "Bounded metadata-only feasibility checks; never operational use.",
        "results": [fetch_probe(spec) for spec in config["probes"]],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("data/source_probes.json"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/reports/source_probe_results.json"),
    )
    parser.add_argument("--manifest", type=Path, default=Path("data/datasets_manifest.json"))
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_manifest(load_json(args.manifest))
    if errors:
        for error in errors:
            print(error)
        return 2
    print(f"manifest valid: {args.manifest}")
    if args.validate_only:
        return 0
    results = run_probes(load_json(args.config))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    successes = sum(bool(item["ok"]) for item in results["results"])
    print(f"probes successful: {successes}/{len(results['results'])}")
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
