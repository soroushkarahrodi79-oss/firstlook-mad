"""Phase 0D.1C payload-free, committable provenance ledger.

``data/raw/phase0d/**`` (third-party bytes and their full sidecars) stays
gitignored -- that does not change here. This module writes a *second*,
metadata-only copy of each sidecar's provenance fields to
``outputs/provenance/phase0d/<probe_id>/<date>.provenance.json``, safe to
commit and reviewable in a PR diff without ever distributing a source's raw
bytes.

A ledger entry never contains a raw response body, an API key, a cookie, or
an anti-forgery token -- see ``FORBIDDEN_KEY_SUBSTRINGS`` and
``build_ledger_entry``, which only copies an explicit allowlist of fields.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"

# Explicit allowlist: only these keys are ever copied from a raw provenance
# sidecar into a committable ledger entry.
_ALLOWED_SIDECAR_FIELDS = (
    "probe_id",
    "source_url",
    "acquired_at_utc",
    "http_status",
    "content_type",
    "byte_count",
    "sha256",
    "truncated",
    "evidence_nature",
    "local_raw_path",
    "parent_probe_id",
    "parent_raw_sha256",
    "parent_acquired_at_utc",
    "resolved_url",
    "hop",
)

# Defence in depth: even though only the allowlist above is ever copied,
# reject a ledger entry outright if any of these ever show up in a value,
# in case a future field is added to the allowlist carelessly.
FORBIDDEN_KEY_SUBSTRINGS = (
    "api_key",
    "apikey",
    "cookie",
    "requestverificationtoken",
    "authorization",
    "password",
    "secret",
    "token",
)


class LedgerSecretGuardError(ValueError):
    """Raised when a ledger entry would carry a forbidden field or value."""


def build_ledger_entry(
    sidecar: dict[str, Any],
    *,
    assumption: str,
    classification: str,
) -> dict[str, Any]:
    """Build a payload-free ledger entry from a raw provenance sidecar dict.

    Only fields in ``_ALLOWED_SIDECAR_FIELDS`` are copied; ``assumption`` and
    ``classification`` are supplied by the caller since raw sidecars (written
    by the acquisition scripts) do not know either.
    """
    entry: dict[str, Any] = {"schema_version": SCHEMA_VERSION}
    for field in _ALLOWED_SIDECAR_FIELDS:
        if field in sidecar:
            entry[field] = sidecar[field]
    entry["assumption"] = assumption
    entry["evidence_classification"] = classification

    _assert_no_forbidden_content(entry)
    return entry


def _assert_no_forbidden_content(entry: dict[str, Any]) -> None:
    serialized = json.dumps(entry).lower()
    for marker in FORBIDDEN_KEY_SUBSTRINGS:
        if marker in serialized:
            raise LedgerSecretGuardError(
                f"ledger entry for probe {entry.get('probe_id')!r} contains "
                f"forbidden marker {marker!r}; refusing to write it"
            )


def ledger_path(ledger_dir: Path, probe_id: str, raw_path: Path) -> Path:
    """Deterministic ledger path mirroring the raw artifact's date-stamped name."""
    return ledger_dir / probe_id / raw_path.name.replace(".raw", ".provenance.json")


def write_ledger_entry(
    ledger_dir: Path,
    sidecar: dict[str, Any],
    *,
    assumption: str,
    classification: str,
) -> Path:
    entry = build_ledger_entry(sidecar, assumption=assumption, classification=classification)
    raw_path = Path(sidecar["local_raw_path"])
    out_path = ledger_path(ledger_dir, sidecar["probe_id"], raw_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path


# probe_id -> (assumption, evidence classification), curated by hand from the
# Phase 0D.1B/0D.1C/0D.1D semantic review -- this is deliberately NOT inferred
# automatically from raw bytes, since classification is an analytical
# judgement call this ledger only records, never makes.
PROBE_CLASSIFICATIONS: dict[str, tuple[str, str]] = {
    "enaire_uas_zones_madrid_bbox": ("A-03", "REAL_BOUNDED_SAMPLE"),
    "madrid_city_open_data_fire_stations": ("A-02", "REAL_SOURCE_DATA"),
    "aemet_madrid_station_inventory": ("A-04", "REAL_WRAPPER"),
    "aemet_madrid_station_inventory_datos": ("A-04", "NOT_USABLE_FOR_TARGET_TEST"),
    "ign_mdt05_madrid_capabilities": ("A-03", "REAL_METADATA"),
    "ign_wcs_mdt_capabilities": ("A-03", "REAL_METADATA"),
    "ign_wcs_mdt_describe_5m": ("A-03", "REAL_METADATA"),
    "ign_mdt05_getcoverage_madrid_sample": ("A-03", "REAL_SOURCE_DATA"),
    "egif_public_search_madrid": ("A-01", "REAL_METADATA"),
    "egif_search_landing_session": ("A-01", "REAL_METADATA"),
    "egif_ccaa_lookup": ("A-01", "REAL_METADATA"),
    "egif_provincia_lookup_madrid": ("A-01", "REAL_METADATA"),
    "egif_search_post_madrid": ("A-01", "REAL_METADATA"),
    "egif_results_page_madrid": ("A-01", "REAL_METADATA"),
}

# Per-artifact overrides keyed by the exact content SHA-256. Used when two
# artifacts share one probe_id but must be classified differently -- the
# classification is still curated by hand and pinned to an exact byte content,
# never guessed from the bytes at ledger time. This lets the honest,
# content-verified classification win over the probe-level default without the
# ledger ever having to parse or re-decode a payload itself.
#
# aemet_madrid_station_inventory_datos has two second-hop artifacts: an early
# 57-byte "datos expirados" 404-in-body (keeps the NOT_USABLE_FOR_TARGET_TEST
# probe default) and the later 167,915-byte real inventory of 926 stations
# (23 in Madrid), verified out-of-band as genuine AEMET station records and
# therefore REAL_SOURCE_DATA. The ISO-8859-15 encoding of that real payload is
# why the acquisition-time UTF-8 classifier could not confirm it; this pin
# records the verified result without re-running acquisition.
ARTIFACT_CLASSIFICATIONS: dict[str, tuple[str, str]] = {
    "fe21a46756675c9febdead0273901c5a2760fa190ff10d107b7ae04695ff0f8e": (
        "A-04",
        "REAL_SOURCE_DATA",
    ),
}


def build_ledger_from_raw_dir(raw_dir: Path, ledger_dir: Path) -> list[Path]:
    """Walk every ``*.raw.provenance.json`` sidecar under ``raw_dir`` and
    write a corresponding payload-free ledger entry. Skips (and reports via
    a printed warning, not a raised error) any probe_id absent from
    ``PROBE_CLASSIFICATIONS`` -- an unclassified artifact should be reviewed
    by a person, not silently guessed at.
    """
    written: list[Path] = []
    for sidecar_path in sorted(raw_dir.glob("*/*.raw.provenance.json")):
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        probe_id = sidecar["probe_id"]
        sha256 = sidecar.get("sha256")
        # A content-pinned override wins over the probe-level default so two
        # artifacts of one probe can carry different, verified classifications.
        if sha256 in ARTIFACT_CLASSIFICATIONS:
            assumption, classification = ARTIFACT_CLASSIFICATIONS[sha256]
        elif probe_id in PROBE_CLASSIFICATIONS:
            assumption, classification = PROBE_CLASSIFICATIONS[probe_id]
        else:
            print(f"WARNING: no curated classification for probe_id={probe_id!r}, skipping")
            continue
        out_path = write_ledger_entry(
            ledger_dir, sidecar, assumption=assumption, classification=classification
        )
        written.append(out_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/phase0d"))
    parser.add_argument("--ledger-dir", type=Path, default=Path("outputs/provenance/phase0d"))
    args = parser.parse_args()

    written = build_ledger_from_raw_dir(args.raw_dir, args.ledger_dir)
    for path in written:
        print(f"wrote: {path}")
    print(f"{len(written)} ledger entries written under {args.ledger_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
