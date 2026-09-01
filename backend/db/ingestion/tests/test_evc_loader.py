"""Dependency-free checks for the Victorian EVC source boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "evc" / "load_evc.py"
SPEC = importlib.util.spec_from_file_location("load_evc", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def feature(
    feature_id: str,
    code: str = "OtR_0030",
    name: str = "Wet Forest",
    status: str = "Least Concern",
    coordinates=None,
) -> dict:
    return {
        "type": "Feature",
        "id": feature_id,
        "properties": {
            "veg_code": code,
            "x_evcname": name,
            "evc_bcs_desc": status,
            "evc_code": "0030",
            "bioregion": "Otway Ranges",
            "bioregion_code": "OtR_",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": coordinates or [[
                [143.0, -38.0], [144.0, -38.0], [144.0, -37.0],
                [143.0, -37.0], [143.0, -38.0],
            ]],
        },
    }


class EvcValidationTests(unittest.TestCase):
    def read(self, features: list[dict]):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.geojson"
            path.write_text(
                json.dumps({"type": "FeatureCollection", "features": features}),
                encoding="utf-8",
            )
            return MODULE.read_and_validate(path)

    def test_accepts_regional_evc_and_preserves_status(self):
        rows = self.read([feature("nv1750_evcbcs.1")])
        self.assertEqual(rows[0][:4], (
            "nv1750_evcbcs.1", "OtR_0030", "Wet Forest", "Least Concern",
        ))

    def test_accepts_multiple_fragments_of_same_regional_evc(self):
        rows = self.read([
            feature("nv1750_evcbcs.1"),
            feature("nv1750_evcbcs.2"),
        ])
        self.assertEqual(len(rows), 2)

    def test_rejects_missing_or_duplicate_source_ids(self):
        with self.assertRaisesRegex(ValueError, "missing/duplicate source id"):
            self.read([feature("duplicate"), feature("duplicate")])

    def test_rejects_missing_regional_code_or_name(self):
        with self.assertRaisesRegex(ValueError, "missing veg_code/x_evcname"):
            self.read([feature("nv1750_evcbcs.1", code="")])

    def test_rejects_inconsistent_metadata_for_regional_code(self):
        with self.assertRaisesRegex(ValueError, "inconsistent name/status"):
            self.read([
                feature("nv1750_evcbcs.1"),
                feature("nv1750_evcbcs.2", status="Vulnerable"),
            ])

    def test_rejects_non_polygon_geometry(self):
        item = feature("nv1750_evcbcs.1")
        item["geometry"] = {"type": "Point", "coordinates": [143.0, -38.0]}
        with self.assertRaisesRegex(ValueError, "not polygon geometry"):
            self.read([item])

    def test_rejects_implausible_epsg4326_coordinates(self):
        with self.assertRaisesRegex(ValueError, "EPSG:4326"):
            self.read([feature("nv1750_evcbcs.1", coordinates=[[[1, 1], [2, 2]]])])


if __name__ == "__main__":
    unittest.main()
