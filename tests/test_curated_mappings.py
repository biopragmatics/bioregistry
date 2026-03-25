"""Test for checking the integrity of the curated_papers TSV file."""

import unittest
from collections import Counter
from typing import Any

import sssom_pydantic

from bioregistry import is_valid_curie
from bioregistry.constants import CURATED_MAPPINGS_PATH
from bioregistry.schema_utils import (
    SemanticMapping,
    read_has_version_mappings,
    read_mappings,
    read_metaregistry,
)


class TestTSV(unittest.TestCase):
    """Tests for curated_mappings tsv file."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.metaregistry = read_metaregistry()

    def validate_row(self, row: dict[str, Any]) -> None:
        """Validate a single row from the TSV file."""
        # Constraints on what prefix has to be used for some columns
        self.assertEqual("orcid", row["creator_id"].split(":")[0])
        self.assertEqual("bioregistry", row["subject_id"].split(":")[0])

        # Check that all CURIE fields are overall valid
        for column in ["subject_id", "predicate_id", "creator_id"]:
            self.assertTrue(is_valid_curie(row[column]))

        # Special handling for metaregistry CURIEs
        object_prefix, _object_id = row["object_id"].split(":", maxsplit=1)
        self.assertIn(object_prefix, self.metaregistry)

        # Make sure we don't have quotes around comments
        if row["comment"] is not None:
            self.assertFalse(row["comment"].startswith('"'))
            self.assertFalse(row["comment"].endswith('"'))

    def test_tsv_file(self) -> None:
        """Tests all rows in TSV file are valid."""
        mappings, _, _ = sssom_pydantic.read(CURATED_MAPPINGS_PATH)
        mapping_counts = Counter((mapping.subject, mapping.object) for mapping in mappings)
        duplicated_mappings = [
            mapping for mapping, count in mapping_counts.most_common() if count > 1
        ]
        if duplicated_mappings:
            summary = "\n".join(
                f"- {subject_id}, {object_id}" for subject_id, object_id in duplicated_mappings
            )
            self.fail(
                msg=f"The following subject-object pairs have multiple curations:\n\n{summary}\n\nI"
                f"f you meant to overwrite an existing curation, delete the old row."
            )
        self.assertEqual(
            sorted(mappings),
            mappings,
            msg=f"""

    The curated mappings in src/bioregistry/data/{CURATED_MAPPINGS_PATH.name}
    were not sorted properly.

    Please lint these files using the following commands in the console:

    $ pip install tox
    $ tox -e bioregistry-lint
            """,
        )


class TestSemanticMappings(unittest.TestCase):
    """Tests to make sure semantic mappings are read correctly from TSV."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.mappings = read_mappings()

    def test_semantic_mappings(self) -> None:
        """Test semantic mapping validity."""
        for mapping in self.mappings:
            self.assertIsInstance(mapping, SemanticMapping)
            self.assertNotEqual(mapping.comment, "")
            self.assertIn(mapping.predicate_modifier, {None, "Not"})

    def test_version_mappings(self) -> None:
        """Test getting mappings that are versions."""
        has_version_mappings = read_has_version_mappings()
        self.assertIn("envo", has_version_mappings)
        self.assertIn("tib", has_version_mappings["envo"])
        self.assertIn("envo2023", has_version_mappings["envo"]["tib"])
