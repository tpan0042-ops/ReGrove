"""Dependency-free tests for local VBA SHP validation and parsing."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "vba" / "load_vba.py"
SPEC = importlib.util.spec_from_file_location("load_vba", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def ogrinfo_output(dataset: str, *, epsg: int = 4283) -> str:
    definition = MODULE.DATASETS[dataset]
    fields = "\n".join(
        f"{name}: {field_type}" + ("" if field_type == "Date" else " (10.0)")
        for name, field_type in definition["fields"].items()
    )
    return (
        f"Layer name: {definition['layer']}\nGeometry: Polygon\nFeature Count: 2\n"
        f'    ID["EPSG",{epsg}]]\n{fields}\n'
    )


def feature(
    *, cell_id: int = 1, taxon_id: int = 2, name: str = "Example species",
    records: int = 3, first: str | None = "2020-01-01",
    last: str | None = "2024-01-01",
) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "CELL_ID": cell_id, "TAXON_ID": taxon_id, "SCI_NAME": name,
            "COMM_NAME": "Example", "RECORDS": records, "FIRST_DATE": first,
            "LAST_DATE": last, "VERS_DATE": "2026051905",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[143.5, -38.8], [143.6, -38.8], [143.5, -38.8]]],
        },
    }


class VbaLoaderTests(unittest.TestCase):
    def shapefile(self, directory: str, name: str = "source.shp") -> Path:
        path = Path(directory) / name
        for extension in (".shp", ".dbf", ".shx", ".prj"):
            path.with_suffix(extension).touch()
        return path

    def test_accepts_actual_flora_schema_and_gda94(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.shapefile(directory)
            completed = subprocess.CompletedProcess([], 0, ogrinfo_output("flora"), "")
            with patch.object(MODULE.subprocess, "run", return_value=completed):
                result = MODULE.inspect_shapefile(path, "flora")
        self.assertEqual(result["feature_count"], 2)
        self.assertEqual(result["crs"], "EPSG:4283")
        self.assertIn("VIC_LF", result["fields"])

    def test_fauna_schema_does_not_contain_flora_lifeform(self):
        self.assertNotIn("VIC_LF", MODULE.DATASETS["fauna"]["fields"])

    def test_rejects_wrong_crs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.shapefile(directory)
            completed = subprocess.CompletedProcess([], 0, ogrinfo_output("fauna", epsg=4326), "")
            with patch.object(MODULE.subprocess, "run", return_value=completed):
                with self.assertRaisesRegex(ValueError, "EPSG:4283"):
                    MODULE.inspect_shapefile(path, "fauna")

    def extract(self, features: list[dict], dataset: str = "flora"):
        stdout = "".join("\x1e" + json.dumps(item) + "\n" for item in features)
        completed = subprocess.CompletedProcess([], 0, stdout, "")
        with patch.object(MODULE.subprocess, "run", return_value=completed):
            return MODULE.extract_bbox_features(
                Path("source.shp"), dataset, (143.0, -39.0, 144.0, -38.0)
            )

    def test_parses_counts_dates_and_taxon_identity(self):
        rows = self.extract([feature()])
        self.assertEqual(rows[0]["taxon_id"], 2)
        self.assertEqual(rows[0]["record_count"], 3)
        self.assertEqual(str(rows[0]["first_date"]), "2020-01-01")

    def test_accepts_paired_missing_flora_dates(self):
        rows = self.extract([feature(first=None, last=None)])
        self.assertIsNone(rows[0]["first_date"])
        self.assertIsNone(rows[0]["last_date"])

    def test_rejects_duplicate_grid_taxon_rows(self):
        with self.assertRaisesRegex(ValueError, "duplicate CELL_ID/TAXON_ID"):
            self.extract([feature(), feature()])

    def test_rejects_reversed_dates(self):
        with self.assertRaisesRegex(ValueError, "inconsistent first/last dates"):
            self.extract([feature(first="2024-01-01", last="2020-01-01")])

    def test_rejects_nonpositive_record_count(self):
        with self.assertRaisesRegex(ValueError, "non-positive RECORDS"):
            self.extract([feature(records=0)], "fauna")


if __name__ == "__main__":
    unittest.main()
