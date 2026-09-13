"""Deterministic JSON serialization, hashing and a tracked-output secret guard."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel

# Mirrors scripts/provenance_ledger.py FORBIDDEN_KEY_SUBSTRINGS: a tracked 0D.2
# output carrying any of these is refused outright.
SECRET_MARKERS = (
    "api_key",
    "apikey",
    "cookie",
    "requestverificationtoken",
    "authorization",
    "password",
    "secret",
    "token",
)


class TrackedOutputLeakError(ValueError):
    """A tracked output would carry a credential-like marker."""


def canonical_json_bytes(model: BaseModel) -> bytes:
    """Sorted keys, two-space indent, UTF-8, LF line endings, trailing newline."""

    text = json.dumps(
        model.model_dump(mode="json"),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def assert_no_secret_markers(data: bytes, *, where: str) -> None:
    lowered = data.decode("utf-8").lower()
    for marker in SECRET_MARKERS:
        if marker in lowered:
            raise TrackedOutputLeakError(
                f"{where}: contains forbidden marker {marker!r}; refusing to emit it"
            )
