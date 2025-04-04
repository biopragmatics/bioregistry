"""Test for checking the integrity of the curated_papers TSV file."""

import unittest
from collections import Counter

from bioregistry import is_valid_curie
from bioregistry.constants import CURATED_MAPPINGS_PATH
from bioregistry.schema_utils import SemanticMapping, read_mappings, read_metaregistry


class TestTSV(unittest.TestCase):
    """Tests for curated_mappings tsv file."""

    def setUp(self):
        """Set up the test case."""
        self.metaregistry = read_metaregistry()

    def validate_row(self, row):
        """Validate a single row from the TSV file."""
        # Constraints on what prefix has to be used for some columns
        self.assertEqual("orcid", row["creator_id"].split(":")[0])
        self.assertEqual("bioregistry", row["subject_id"].split(":")[0])

        # Check that all CURIE fields are overall valid
        for column in ["subject_id", "predicate_id", "creator_id"]:
            self.assertTrue(is_valid_curie(row[column]))

        # Special handling for metaregistry CURIEs
        object_prefix, object_id = row["object_id"].split(":", maxsplit=1)
        self.assertIn(object_prefix, self.metaregistry)

        # Make sure we don't have quotes around comments
        if row["comment"] is not None:
            self.assertFalse(row["comment"].startswith('"'))
            self.assertFalse(row["comment"].endswith('"'))

    def test_tsv_file(self):
        """Tests all rows in TSV file are valid."""
        with CURATED_MAPPINGS_PATH.open() as tsv_file:
            mapping_keys = []
            header = next(tsv_file).strip("\n").split("\t")
            for row, line in enumerate(tsv_file, start=2):
                with self.subTest(row=row, line=line):
                    line = line.strip("\n").split("\t")
                    self.assertEqual(
                        len(header),
                        len(line),
                        msg="Wrong number of columns. This is usually due to the wrong amount of trailing tabs.",
                    )
                    data = dict(zip(header, line))
                    self.validate_row(data)
                    mapping_keys.append(
                        (
                            data["subject_id"],
                            data["object_id"],
                            data["predicate_id"],
                            data["predicate_modifier"],
                        )
                    )

            mapping_counts = Counter(
                (subject_id, object_id) for subject_id, object_id, _, _ in mapping_keys
            )
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
                sorted(mapping_keys),
                mapping_keys,
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

    def setUp(self):
        """Set up the test case."""
        self.mappings = read_mappings()

    def test_semantic_mappings(self):
        """Test semantic mapping validity."""
        for mapping in self.mappings:
            self.assertIsInstance(mapping, SemanticMapping)
            self.assertNotEqual(mapping.comment, "")
            self.assertIn(mapping.predicate_modifier, {None, "Not"})
