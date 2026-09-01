"""Opt-in database idempotence check for a real cached VicFlora name list."""

from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "plants" / "load_vicflora_plants.py"
SPEC = importlib.util.spec_from_file_location("load_vicflora_plants_integration", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(
    os.getenv("REGROVE_PLANT_INTEGRATION") == "1",
    "set REGROVE_PLANT_INTEGRATION=1 for the real database check",
)
class VicFloraPlantIntegrationTests(unittest.TestCase):
    def test_repeated_load_preserves_species_and_trait_sets(self):
        input_path = Path(os.environ["REGROVE_VICFLORA_INPUT"])
        cache_path = Path(os.environ["REGROVE_VICFLORA_CACHE"])
        with tempfile.TemporaryDirectory() as directory:
            args = Namespace(
                input=input_path,
                cache=cache_path,
                report=Path(directory) / "report.csv",
                refresh=False,
                offline=True,
                verbose=False,
            )
            first_results, first_species, first_traits = MODULE.run(args)
            second_results, second_species, second_traits = MODULE.run(args)
        self.assertEqual(first_species, second_species)
        self.assertEqual(first_traits, second_traits)
        self.assertEqual(first_results, second_results)

        config = MODULE.DatabaseConfig.from_environment()
        duplicate_count = int(MODULE.run_psql(
            config,
            """
            SELECT count(*) FROM (
                SELECT t.plant_species_id, t.source_id, t.trait_name
                FROM plant_trait t
                JOIN source s ON s.source_id = t.source_id
                WHERE s.source_name = 'VicFlora taxonomy'
                GROUP BY t.plant_species_id, t.source_id, t.trait_name
                HAVING count(*) > 1
            ) duplicates;
            """,
        ))
        self.assertEqual(duplicate_count, 0)


if __name__ == "__main__":
    unittest.main()
