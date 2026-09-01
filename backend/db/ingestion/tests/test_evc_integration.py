"""Opt-in real-source/PostGIS integration checks for the EVC loader."""

from __future__ import annotations

import argparse
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "evc" / "load_evc.py"
SPEC = importlib.util.spec_from_file_location("load_evc_integration", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(
    os.getenv("REGROVE_EVC_INTEGRATION") == "1",
    "set REGROVE_EVC_INTEGRATION=1 against a migrated database with postcode 3233",
)
class EvcIntegrationTests(unittest.TestCase):
    def test_real_3233_spatial_load_is_idempotent(self):
        config = MODULE.DatabaseConfig.from_environment()
        cache_value = os.getenv("REGROVE_EVC_CACHE_DIR")
        temporary = None
        if cache_value:
            cache_dir = Path(cache_value)
        else:
            temporary = tempfile.TemporaryDirectory()
            cache_dir = Path(temporary.name)
        self.addCleanup(lambda: temporary and temporary.cleanup())

        postcodes = MODULE.database_postcodes(config, ["3233"])
        args = argparse.Namespace(
            cache_dir=cache_dir,
            refresh=False,
            offline=False,
        )
        for year in (1750, 2005):
            MODULE.run_dataset(config, year, postcodes, args)

        first = MODULE.run_psql(
            config,
            """
            SELECT reference_year || '|' || count(*) || '|' ||
                   count(DISTINCT evc_id) || '|' ||
                   min(overlap_percent) || '|' || max(overlap_percent)
            FROM postcode_evc_context
            WHERE postcode = '3233'
              AND source_id IN (
                  SELECT source_id FROM (
                      SELECT DISTINCT ON (source_name) source_id
                      FROM source
                      WHERE source_name LIKE 'DEECA NV% EVC with Bioregional Conservation Status'
                      ORDER BY source_name, source_id DESC
                  ) current_sources
              )
              AND reference_year IN (1750, 2005)
            GROUP BY reference_year ORDER BY reference_year;
            """,
        )
        for year in (1750, 2005):
            MODULE.run_dataset(config, year, postcodes, args)
        second = MODULE.run_psql(
            config,
            """
            SELECT reference_year || '|' || count(*) || '|' ||
                   count(DISTINCT evc_id) || '|' ||
                   min(overlap_percent) || '|' || max(overlap_percent)
            FROM postcode_evc_context
            WHERE postcode = '3233'
              AND source_id IN (
                  SELECT source_id FROM (
                      SELECT DISTINCT ON (source_name) source_id
                      FROM source
                      WHERE source_name LIKE 'DEECA NV% EVC with Bioregional Conservation Status'
                      ORDER BY source_name, source_id DESC
                  ) current_sources
              )
              AND reference_year IN (1750, 2005)
            GROUP BY reference_year ORDER BY reference_year;
            """,
        )

        self.assertEqual(first, second)
        rows = [line.split("|") for line in first.splitlines()]
        self.assertEqual([row[0] for row in rows], ["1750", "2005"])
        for _, count, distinct_count, minimum, maximum in rows:
            self.assertGreater(int(count), 0)
            self.assertEqual(count, distinct_count)
            self.assertGreaterEqual(float(minimum), 0)
            self.assertLessEqual(float(maximum), 100)


if __name__ == "__main__":
    unittest.main()
