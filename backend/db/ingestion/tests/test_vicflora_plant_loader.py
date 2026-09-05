"""Dependency-free tests for strict VicFlora plant-name resolution."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "plants" / "load_vicflora_plants.py"
SPEC = importlib.util.spec_from_file_location("load_vicflora_plants", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def accepted(
    name: str = "Acacia melanoxylon",
    *,
    concept_id: str = "accepted-1",
    common_name: str | None = "Blackwood",
    dual_status: bool | None = None,
) -> dict:
    return {
        "id": concept_id,
        "taxonRank": "SPECIES",
        "taxonomicStatus": "ACCEPTED",
        "occurrenceStatus": "PRESENT",
        "establishmentMeans": "NATIVE",
        "degreeOfEstablishment": "NATIVE",
        "endemic": None,
        "hasIntroducedOccurrences": dual_status,
        "epbc": None,
        "ffg": None,
        "taxonName": {"fullName": name},
        "preferredVernacularName": {"name": common_name} if common_name else None,
    }


def taxon_name(
    supplied: str,
    target: dict,
    *,
    status: str = "ACCEPTED",
) -> dict:
    concept = dict(target)
    concept.update(
        id=f"source-{supplied}",
        taxonomicStatus=status,
        taxonName={"fullName": supplied},
        acceptedConcept=target,
    )
    return {
        "id": f"name-{supplied}",
        "fullName": supplied,
        "rank": "SPECIES",
        "taxonConcepts": [concept],
    }


class VicFloraResolutionTests(unittest.TestCase):
    def test_exact_accepted_species(self):
        row = MODULE.resolve_name(
            "Acacia melanoxylon", "Acacia melanoxylon",
            [taxon_name("Acacia melanoxylon", accepted())],
        )
        self.assertEqual(row["resolution_result"], "exact_accepted")
        self.assertEqual(row["accepted_name"], "Acacia melanoxylon")
        self.assertEqual(row["common_name"], "Blackwood")
        self.assertEqual(row["native_status"], "Victorian native")

    def test_synonym_resolves_to_accepted_species(self):
        target = accepted("Hackelia latifolia", concept_id="accepted-hackelia", common_name=None)
        row = MODULE.resolve_name(
            "Austrocynoglossum latifolium", "Austrocynoglossum latifolium",
            [taxon_name(
                "Austrocynoglossum latifolium", target,
                status="HOMOTYPIC_SYNONYM",
            )],
        )
        self.assertEqual(row["resolution_result"], "synonym_resolved")
        self.assertEqual(row["accepted_name"], "Hackelia latifolia")

    def test_prefix_result_is_not_an_exact_match(self):
        row = MODULE.resolve_name(
            "Hydrocotyle spp.", "Hydrocotyle spp.",
            [taxon_name("Hydrocotyle hirta", accepted("Hydrocotyle hirta"))],
        )
        self.assertEqual(row["resolution_result"], "unresolved")

    def test_multiple_accepted_concepts_are_ambiguous(self):
        first = taxon_name("Example plant", accepted("Example alpha", concept_id="a"))
        second = taxon_name("Example plant", accepted("Example beta", concept_id="b"))
        first["taxonConcepts"].extend(second["taxonConcepts"])
        row = MODULE.resolve_name("Example plant", "Example plant", [first])
        self.assertEqual(row["resolution_result"], "ambiguous")
        self.assertIn("Example alpha", row["notes"])
        self.assertIn("Example beta", row["notes"])

    def test_non_species_accepted_concept_is_not_loadable(self):
        target = accepted("Acacia example subsp. minor")
        target["taxonRank"] = "SUBSPECIES"
        row = MODULE.resolve_name(
            "Acacia example subsp. minor", "Acacia example subsp. minor",
            [taxon_name("Acacia example subsp. minor", target)],
        )
        self.assertEqual(row["resolution_result"], "non_species_rank")
        self.assertEqual(MODULE.rows_for_database([row]), ([], []))

    def test_dual_native_and_introduced_status_is_preserved(self):
        target = accepted(dual_status=True)
        row = MODULE.resolve_name(
            "Acacia melanoxylon", "Acacia melanoxylon",
            [taxon_name("Acacia melanoxylon", target)],
        )
        self.assertEqual(
            row["native_status"],
            "Victorian native; introduced occurrences also recorded",
        )
        self.assertEqual(row["has_introduced_occurrences"], "true")

    def test_unknown_status_is_not_fabricated(self):
        target = accepted()
        target["degreeOfEstablishment"] = None
        row = MODULE.resolve_name(
            "Acacia melanoxylon", "Acacia melanoxylon",
            [taxon_name("Acacia melanoxylon", target)],
        )
        self.assertEqual(row["native_status"], "")

    def test_duplicate_input_is_reported_and_not_loaded_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "names.txt"
            path.write_text(
                "Acacia melanoxylon\nAcacia melanoxylon\n",
                encoding="utf-8",
            )
            inputs = MODULE.read_name_list(path)
        responses = {
            "Acacia melanoxylon": [taxon_name("Acacia melanoxylon", accepted())]
        }
        rows = MODULE.resolve_rows(inputs, responses)
        self.assertEqual(
            [row["resolution_result"] for row in rows],
            ["exact_accepted", "duplicate_input"],
        )
        plants, traits = MODULE.rows_for_database(rows)
        self.assertEqual(len(plants), 1)
        self.assertGreater(len(traits), 0)
        self.assertEqual(len({(row[0], row[1]) for row in traits}), len(traits))

    def test_reviewed_query_name_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "names.tsv"
            path.write_text(
                "Original misspelling\tAcacia melanoxylon\n",
                encoding="utf-8",
            )
            item = MODULE.read_name_list(path)[0]
        row = MODULE.resolve_name(
            item["original_name"], item["query_name"],
            [taxon_name("Acacia melanoxylon", accepted())],
        )
        self.assertEqual(row["original_name"], "Original misspelling")
        self.assertEqual(row["query_name"], "Acacia melanoxylon")
        self.assertIn("reviewed input", row["notes"])


if __name__ == "__main__":
    unittest.main()
