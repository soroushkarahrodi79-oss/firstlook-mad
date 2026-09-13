from __future__ import annotations

import io
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock

from scripts.acquire_phase0d_ign_mdt import run_ign_mdt_discovery

CAPABILITIES_WITH_5M = b"""<?xml version="1.0"?>
<wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0" xmlns:ows="http://www.opengis.net/ows/2.0">
  <ows:ServiceIdentification>
    <ows:Title>Modelos Digitales del Terreno de Espa\xc3\xb1a</ows:Title>
    <ows:Abstract>MDT de 5, 25, 200, 500 y 1000 m.</ows:Abstract>
  </ows:ServiceIdentification>
  <wcs:Contents>
    <wcs:CoverageSummary><wcs:CoverageId>Elevacion4258_1000</wcs:CoverageId></wcs:CoverageSummary>
    <wcs:CoverageSummary><wcs:CoverageId>Elevacion25830_5</wcs:CoverageId></wcs:CoverageSummary>
    <wcs:CoverageSummary><wcs:CoverageId>Elevacion4083_5</wcs:CoverageId></wcs:CoverageSummary>
  </wcs:Contents>
</wcs:Capabilities>
"""

CAPABILITIES_WITHOUT_5M = b"""<?xml version="1.0"?>
<wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0" xmlns:ows="http://www.opengis.net/ows/2.0">
  <wcs:Contents>
    <wcs:CoverageSummary><wcs:CoverageId>Elevacion4258_1000</wcs:CoverageId></wcs:CoverageSummary>
  </wcs:Contents>
</wcs:Capabilities>
"""

DESCRIBE_COVERAGE_XML = b"""<?xml version="1.0"?>
<wcs:CoverageDescriptions xmlns:wcs="http://www.opengis.net/wcs/2.0" xmlns:gml="http://www.opengis.net/gml/3.2">
  <wcs:CoverageDescription gml:id="Elevacion25830_5">
    <gml:boundedBy>
      <gml:Envelope srsName="http://www.opengis.net/def/crs/EPSG/0/25830"
                    axisLabels="x y" uomLabels="m m" srsDimension="2">
        <gml:lowerCorner>-19452.5 3901197.5</gml:lowerCorner>
        <gml:upperCorner>1140352.5 4865682.5</gml:upperCorner>
      </gml:Envelope>
    </gml:boundedBy>
    <gml:offsetVector srsName="x">5.000000 0</gml:offsetVector>
    <gml:offsetVector srsName="y">0 -5.000000</gml:offsetVector>
  </wcs:CoverageDescription>
</wcs:CoverageDescriptions>
"""


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = io.BytesIO(body)
        self.status = status
        self.headers = {"Content-Type": "application/xml"}

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class RunIgnMdtDiscoveryTests(unittest.TestCase):
    def test_5m_coverage_found_triggers_describe_coverage(self) -> None:
        opener = Mock(
            side_effect=[FakeResponse(CAPABILITIES_WITH_5M), FakeResponse(DESCRIBE_COVERAGE_XML)]
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_ign_mdt_discovery(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,
            )
        caps = result["capabilities"]
        self.assertTrue(caps["mdt05_available"])
        self.assertIn("Elevacion25830_5", caps["mdt05_equivalent_coverage_ids"])
        self.assertEqual(caps["classification"], "REAL_METADATA")

        describe = result["describe_coverage"]
        self.assertEqual(describe["outcome"], "ACQUIRED")
        self.assertEqual(describe["crs"], "http://www.opengis.net/def/crs/EPSG/0/25830")
        self.assertEqual(describe["lower_corner"], "-19452.5 3901197.5")
        self.assertIn("5.000000 0", describe["grid_offset_vectors_m"])
        self.assertEqual(opener.call_count, 2)

    def test_no_5m_coverage_skips_describe_coverage(self) -> None:
        opener = Mock(return_value=FakeResponse(CAPABILITIES_WITHOUT_5M))
        with tempfile.TemporaryDirectory() as tmp:
            result = run_ign_mdt_discovery(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,
            )
        self.assertFalse(result["capabilities"]["mdt05_available"])
        self.assertEqual(result["describe_coverage"]["outcome"], "NOT_ATTEMPTED")
        self.assertEqual(opener.call_count, 1)

    def test_capabilities_http_error_is_classified_not_fabricated(self) -> None:
        opener = Mock(
            side_effect=urllib.error.HTTPError(
                "https://servicios.idee.es/wcs-inspire/mdt", 502, "Bad Gateway", {}, None
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = run_ign_mdt_discovery(
                raw_dir=Path(tmp),
                config_consulted_at="2026-08-31T10:00:00+02:00",
                opener=opener,
            )
        self.assertEqual(result["capabilities"]["outcome"], "HTTP_ERROR")
        self.assertNotIn("mdt05_available", result["capabilities"])


if __name__ == "__main__":
    unittest.main()
