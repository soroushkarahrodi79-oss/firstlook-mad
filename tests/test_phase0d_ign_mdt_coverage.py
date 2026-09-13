from __future__ import annotations

import io
import struct
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock

from scripts.acquire_phase0d_ign_mdt_coverage import (
    GETCOVERAGE_PROBE_ID,
    GETCOVERAGE_URL,
    run_ign_mdt_getcoverage_sample,
)


def _minimal_geotiff() -> bytes:
    """A tiny but structurally valid little-endian TIFF header + one strip.

    Only the leading magic matters for classification, but a realistic body
    keeps the test honest about what "looks like a raster" means.
    """
    header = b"II" + struct.pack("<H", 42) + struct.pack("<I", 8)
    # A single (bogus but well-formed) IFD with zero entries, then strip bytes.
    ifd = struct.pack("<H", 0) + struct.pack("<I", 0)
    return header + ifd + b"\x00\x10" * 8


SERVICE_EXCEPTION_XML = (
    b'<?xml version="1.0"?>'
    b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows/2.0" version="2.0.1">'
    b'<ows:Exception exceptionCode="InvalidSubsetting">'
    b"<ows:ExceptionText>subset out of range</ows:ExceptionText>"
    b"</ows:Exception></ows:ExceptionReport>"
)


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, content_type: str = "image/tiff"):
        self._body = io.BytesIO(body)
        self.status = status
        self.headers = {"Content-Type": content_type}

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class RunGetCoverageSampleTests(unittest.TestCase):
    def test_geotiff_body_is_classified_real_and_persisted(self) -> None:
        body = _minimal_geotiff()
        opener = Mock(return_value=FakeResponse(body))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_ign_mdt_getcoverage_sample(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,
            )
            self.assertEqual(result["outcome"], "ACQUIRED")
            self.assertEqual(result["classification"], "REAL_SOURCE_DATA")
            self.assertTrue(result["is_geotiff"])
            self.assertEqual(result["byte_count"], len(body))
            self.assertFalse(result["truncated"])
            raw_path = Path(result["raw_path"])
            self.assertTrue(raw_path.exists())
            self.assertEqual(raw_path.read_bytes(), body)
        self.assertEqual(opener.call_count, 1)

    def test_exactly_one_bounded_request_to_the_verified_coverage(self) -> None:
        opener = Mock(return_value=FakeResponse(_minimal_geotiff()))
        with tempfile.TemporaryDirectory() as tmp:
            run_ign_mdt_getcoverage_sample(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,
            )
        self.assertEqual(opener.call_count, 1)
        requested_url = opener.call_args.args[0].full_url
        self.assertEqual(requested_url, GETCOVERAGE_URL)
        self.assertIn("request=GetCoverage", requested_url)
        self.assertIn("coverageId=Elevacion25830_5", requested_url)
        self.assertIn("subset=x(440000,440100)", requested_url)
        self.assertIn("subset=y(4474000,4474100)", requested_url)

    def test_service_exception_is_classified_honestly_not_as_raster(self) -> None:
        opener = Mock(return_value=FakeResponse(SERVICE_EXCEPTION_XML, content_type="text/xml"))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_ign_mdt_getcoverage_sample(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,
            )
        self.assertEqual(result["outcome"], "ACQUIRED")
        self.assertEqual(result["classification"], "SERVICE_EXCEPTION")
        self.assertFalse(result["is_geotiff"])

    def test_http_error_is_classified_and_persists_nothing(self) -> None:
        opener = Mock(
            side_effect=urllib.error.HTTPError(GETCOVERAGE_URL, 400, "Bad Request", {}, None)
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_ign_mdt_getcoverage_sample(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,
            )
            probe_dir = Path(tmp) / GETCOVERAGE_PROBE_ID
            self.assertFalse(probe_dir.exists())
        self.assertEqual(result["outcome"], "HTTP_ERROR")
        self.assertIsNone(result["classification"])
        self.assertIsNone(result["raw_path"])
        self.assertIsNone(result["sha256"])

    def test_empty_body_is_not_acquired(self) -> None:
        opener = Mock(return_value=FakeResponse(b""))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_ign_mdt_getcoverage_sample(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,
            )
        self.assertEqual(result["outcome"], "EMPTY_RESPONSE")
        self.assertIsNone(result["raw_path"])


if __name__ == "__main__":
    unittest.main()
