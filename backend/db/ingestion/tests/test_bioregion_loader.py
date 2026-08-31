"""Dependency-free checks for the IBRA source boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "bioregion" / "load_bioregions.py"
SPEC = importlib.util.spec_from_file_location("load_bioregions", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def feature(code: str, name: str = "Test Region", coordinates=None) -> dict:
    return {
        "type": "Feature",
        "properties": {"REG_CODE_7": code, "REG_NAME_7": name, "HECTARES": 1.0},
        "geometry": {
            "type": "Polygon",
            "coordinates": coordinates
            or [[[143.0, -38.0], [144.0, -38.0], [144.0, -37.0], [143.0, -38.0]]],
        },
    }


class BioregionValidationTests(unittest.TestCase):
    def read(self, features: list[dict], expected_count: int):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.geojson"
            path.write_text(
                json.dumps({"type": "FeatureCollection", "features": features}),
                encoding="utf-8",
            )
            return MODULE.read_and_validate(path, expected_count)

    def test_accepts_one_ibra_region(self):
        rows = self.read([feature("TST")], 1)
        self.assertEqual(rows[0][:2], ("TST", "Test Region"))

    def test_rejects_duplicate_codes(self):
        with self.assertRaisesRegex(ValueError, "duplicate IBRA region code"):
            self.read([feature("AAA", "Alpha"), feature("AAA", "Beta")], 2)

    def test_rejects_duplicate_names(self):
        with self.assertRaisesRegex(ValueError, "duplicate IBRA region name"):
            self.read([feature("AAA"), feature("BBB")], 2)

    def test_rejects_invalid_geometry_coordinates(self):
        with self.assertRaisesRegex(ValueError, "EPSG:4326"):
            self.read([feature("TST", coordinates=[[[1_000_000, 1_000_000]]])], 1)

    def test_enforces_version_specific_count(self):
        with self.assertRaisesRegex(ValueError, "expected 2"):
            self.read([feature("TST")], 2)


if __name__ == "__main__":
    unittest.main()
