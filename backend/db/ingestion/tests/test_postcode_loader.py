"""Dependency-free checks for the postcode source boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "postcode" / "load_postcodes.py"
SPEC = importlib.util.spec_from_file_location("load_postcodes", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def feature(code: str, coordinates=None) -> dict:
    return {
        "type": "Feature",
        "properties": {"poa_code_2021": code},
        "geometry": {
            "type": "Polygon",
            "coordinates": coordinates
            or [[[143.0, -38.0], [144.0, -38.0], [144.0, -37.0], [143.0, -38.0]]],
        },
    }


class PostcodeValidationTests(unittest.TestCase):
    def read(self, features: list[dict], expected_count: int):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.geojson"
            path.write_text(
                json.dumps({"type": "FeatureCollection", "features": features}),
                encoding="utf-8",
            )
            return MODULE.read_and_validate(path, expected_count)

    def test_accepts_one_victorian_postal_area(self):
        rows = self.read([feature("3233")], 1)
        self.assertEqual(rows[0][0], "3233")

    def test_rejects_duplicate_postcodes(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.read([feature("3233"), feature("3233")], 2)

    def test_rejects_non_victorian_code(self):
        with self.assertRaisesRegex(ValueError, "non-Victorian"):
            self.read([feature("2000")], 1)

    def test_rejects_non_geographic_coordinates(self):
        with self.assertRaisesRegex(ValueError, "EPSG:4326"):
            self.read([feature("3233", [[[1_000_000, 1_000_000]]])], 1)

    def test_enforces_version_specific_count(self):
        with self.assertRaisesRegex(ValueError, "expected 2"):
            self.read([feature("3233")], 2)


if __name__ == "__main__":
    unittest.main()
