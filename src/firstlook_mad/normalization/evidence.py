"""Integrity-verified loading of Phase 0D.1 evidence.

The chain checked for every artifact is: committed payload-free ledger entry
(``outputs/provenance/phase0d/``) -> gitignored raw sidecar -> gitignored raw
bytes (``data/raw/phase0d/``). Bytes reach a normalizer only when all three
SHA-256 values agree; otherwise the artifact stays unverified and unknown.
"""

from __future__ import annotations

import hashlib
import json
import string
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from firstlook_mad.domain import FrozenModel
from firstlook_mad.normalization.models import Integrity, MalformedEvidenceError

LEDGER_SUFFIX = ".provenance.json"
RAW_SUFFIX = ".raw"
SHA256_HEX_LENGTH = 64
REQUIRED_LEDGER_FIELDS = (
    "probe_id",
    "source_url",
    "acquired_at_utc",
    "byte_count",
    "sha256",
    "truncated",
    "local_raw_path",
    "assumption",
    "evidence_classification",
)


class ArtifactEvidence(FrozenModel):
    """Payload-free description of one acquired artifact and its integrity state."""

    probe_id: str
    artifact_name: str
    assumption: str
    ledger_classification: str
    source_url: str
    content_type: str | None
    acquired_at_utc: str
    sha256: str
    byte_count: int
    integrity: Integrity
    integrity_detail: str

    @property
    def ref(self) -> str:
        return f"{self.probe_id}/{self.artifact_name}"


@dataclass(frozen=True)
class LoadedArtifact:
    """An artifact description plus its bytes, present only when integrity is PASS."""

    evidence: ArtifactEvidence
    verified_bytes: bytes | None


def load_evidence(ledger_dir: Path, raw_dir: Path) -> tuple[LoadedArtifact, ...]:
    """Load every ledger entry in deterministic (probe_id, file name) order."""

    if not ledger_dir.is_dir():
        raise MalformedEvidenceError(f"ledger directory not found: {ledger_dir.as_posix()}")
    ledger_files = sorted(
        ledger_dir.glob(f"*/*{LEDGER_SUFFIX}"), key=lambda path: (path.parent.name, path.name)
    )
    if not ledger_files:
        raise MalformedEvidenceError("ledger directory holds no provenance entries")
    return tuple(load_artifact(path, raw_dir) for path in ledger_files)


def load_artifact(ledger_file: Path, raw_dir: Path) -> LoadedArtifact:
    where = f"{ledger_file.parent.name}/{ledger_file.name}"
    entry = read_json_object(ledger_file, where=where)
    missing = [field for field in REQUIRED_LEDGER_FIELDS if field not in entry]
    if missing:
        raise MalformedEvidenceError(f"{where}: ledger entry lacks required fields {missing}")

    probe_id = _str_field(entry, "probe_id", where)
    if probe_id != ledger_file.parent.name:
        raise MalformedEvidenceError(f"{where}: probe_id does not match its ledger directory")
    raw_name = PurePosixPath(_str_field(entry, "local_raw_path", where)).name
    expected_ledger_name = raw_name.removesuffix(RAW_SUFFIX) + LEDGER_SUFFIX
    if not raw_name.endswith(RAW_SUFFIX) or ledger_file.name != expected_ledger_name:
        raise MalformedEvidenceError(f"{where}: ledger name does not mirror its raw artifact")

    sha256 = _str_field(entry, "sha256", where).lower()
    if len(sha256) != SHA256_HEX_LENGTH or any(char not in string.hexdigits for char in sha256):
        raise MalformedEvidenceError(f"{where}: sha256 is not a 64-character hex digest")
    byte_count, truncated = entry["byte_count"], entry["truncated"]
    if isinstance(byte_count, bool) or not isinstance(byte_count, int):
        raise MalformedEvidenceError(f"{where}: byte_count must be an integer")
    if not isinstance(truncated, bool):
        raise MalformedEvidenceError(f"{where}: truncated must be a boolean")
    content_type = entry.get("content_type")
    if content_type is not None and not isinstance(content_type, str):
        raise MalformedEvidenceError(f"{where}: content_type must be a string or null")

    integrity, detail, data = _verify_chain(
        raw_dir / probe_id / raw_name, sha256=sha256, byte_count=byte_count, truncated=truncated
    )
    evidence = ArtifactEvidence(
        probe_id=probe_id,
        artifact_name=raw_name,
        assumption=_str_field(entry, "assumption", where),
        ledger_classification=_str_field(entry, "evidence_classification", where),
        source_url=_str_field(entry, "source_url", where),
        content_type=content_type,
        acquired_at_utc=_str_field(entry, "acquired_at_utc", where),
        sha256=sha256,
        byte_count=byte_count,
        integrity=integrity,
        integrity_detail=detail,
    )
    return LoadedArtifact(evidence=evidence, verified_bytes=data)


def _verify_chain(
    raw_path: Path, *, sha256: str, byte_count: int, truncated: bool
) -> tuple[Integrity, str, bytes | None]:
    if not raw_path.is_file():
        return Integrity.RAW_UNAVAILABLE, "local raw bytes not present", None
    data = raw_path.read_bytes()
    sidecar_path = raw_path.with_name(raw_path.name + LEDGER_SUFFIX)
    sidecar_sha = (
        read_json_object(sidecar_path, where=sidecar_path.name).get("sha256")
        if sidecar_path.is_file()
        else None
    )
    checks = (
        (hashlib.sha256(data).hexdigest() == sha256, "raw SHA-256 differs from ledger"),
        (len(data) == byte_count, "raw byte count differs from ledger"),
        (not truncated, "ledger marks the response as truncated"),
        (sidecar_sha == sha256, "raw sidecar missing or its SHA-256 differs from ledger"),
    )
    failures = [message for passed, message in checks if not passed]
    if failures:
        return Integrity.FAIL, "; ".join(failures), None
    return Integrity.PASS, "raw bytes, sidecar and ledger SHA-256 agree", data


def read_json_object(path: Path, *, where: str) -> dict[str, object]:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MalformedEvidenceError(f"{where}: unreadable JSON ({type(exc).__name__})") from exc
    if not isinstance(payload, dict):
        raise MalformedEvidenceError(f"{where}: expected a JSON object")
    return payload


def _str_field(entry: dict[str, object], key: str, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise MalformedEvidenceError(f"{where}: field {key!r} must be a non-empty string")
    return value


def declared_charset(content_type: str | None, default: str = "utf-8") -> str:
    """Charset declared by the source's Content-Type header; never guessed from bytes."""

    if content_type:
        for parameter in content_type.split(";")[1:]:
            key, _, value = parameter.strip().partition("=")
            if key.lower() == "charset" and value.strip():
                return value.strip().strip('"').lower()
    return default


def decode_json_payload(data: bytes, *, content_type: str | None, where: str) -> object:
    charset = declared_charset(content_type)
    try:
        payload: object = json.loads(data.decode(charset))
    except (LookupError, ValueError) as exc:
        raise MalformedEvidenceError(
            f"{where}: payload is not valid JSON in declared charset {charset!r} "
            f"({type(exc).__name__})"
        ) from exc
    return payload
