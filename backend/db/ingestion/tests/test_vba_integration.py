"""Opt-in real SHP/PostGIS test for VBA postcode aggregation and reruns."""

from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "vba" / "load_vba.py"
SPEC = importlib.util.spec_from_file_location("load_vba_integration", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(
    os.getenv("REGROVE_VBA_INTEGRATION") == "1",
    "set REGROVE_VBA_INTEGRATION=1 for real local-SHP/PostGIS checks",
)
class VbaIntegrationTests(unittest.TestCase):
    def test_real_3233_loads_are_idempotent(self):
        config = MODULE.DatabaseConfig.from_environment()
        postcodes = ["3233"]
        with tempfile.TemporaryDirectory() as directory:
            for dataset, variable in (
                ("flora", "REGROVE_VBA_FLORA_SHP"),
                ("fauna", "REGROVE_VBA_FAUNA_SHP"),
            ):
                path = Path(os.environ[variable])
                MODULE.inspect_shapefile(path, dataset)
                rows = MODULE.extract_bbox_features(
                    path, dataset, MODULE.postcode_bbox(config, postcodes)
                )
                source = {
                    "name": MODULE.DATASETS[dataset]["source_name"],
                    "provider": MODULE.PROVIDER, "url": MODULE.DATASETS[dataset]["url"],
                    "licence": MODULE.LICENCE,
                    "version": f"integration test {rows[0]['version']}",
                }
                source_id = MODULE.register_source(config, source)
                first = MODULE.load_rows(config, dataset, source_id, postcodes, rows)
                second = MODULE.load_rows(config, dataset, source_id, postcodes, rows)
                self.assertEqual(first, second)
                self.assertGreater(first["intersecting_features"], 0)
                self.assertGreater(first["distinct_intersecting_taxa"], 0)
                report = Path(directory) / f"{dataset}.csv"
                MODULE.write_report(report, dataset, first["taxa"])
                self.assertGreater(report.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
