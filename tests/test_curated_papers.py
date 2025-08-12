"""Test for checking the integrity of the curated_papers TSV file."""

import unittest
from collections import Counter
from datetime import datetime

from bioregistry.constants import CURATED_PAPERS_PATH, ORCID_PATTERN
from bioregistry.curation.literature import COLUMNS, CurationRelevance


class TestTSV(unittest.TestCase):
    """Tests for curated_papers tsv file."""

    def setUp(self):
        """Set up the test case."""
        self.relevancy_types = {r.name for r in CurationRelevance}

    def validate_row(self, row):
        """Validate a single row from the TSV file."""
        for field in COLUMNS:
            self.assertIn(field, row)

        self.assertTrue(row["pubmed"].isdigit(), msg="PubMed identifier should be an integer")

        pr_message = (
            "Please include the pull request in which the curation row "
            "was added, written as an integer."
        )
        self.assertIsNotNone(row["pr_added"], msg=pr_message)
        self.assertTrue(row["pr_added"].isdigit(), msg=pr_message)

        # Validate relevant is 0 or 1
        self.assertIn(row["relevant"], ["0", "1"])

        """
        Commenting out this check for now. This can be re-implemented if a need
        for it arises in the future

        if row["relevant"] == "1":
            prefix = row["prefix"]
            self.assertIsNotNone(prefix, msg="prefix should be set for all relevant entries")
            self.assertNotEqual("", prefix, msg="prefix should not be empty for relevant entries")
            self.assertEqual(
                bioregistry.normalize_prefix(prefix),
                prefix,
                msg="prefix should be standardized for relevant entries",
            )
        """

        # Validate relevancy_type is in relevancy_vocab
        self.assertIn(row["relevancy_type"], self.relevancy_types)

        self.assertRegex(row["orcid"], ORCID_PATTERN)

        # Handle None values for notes
        if row["notes"] is not None:
            self.assertFalse(row["notes"].startswith('"'))
            self.assertFalse(row["notes"].endswith('"'))

        # Validate date_curated format
        try:
            datetime.strptime(row["date_curated"], "%Y-%m-%d")
        except ValueError:
            self.fail("date_curated should follow format YYYY-MM-DD")

    def test_tsv_file(self):
        """Tests all rows in TSV file are valid."""
        with CURATED_PAPERS_PATH.open() as tsv_file:
            pubmeds = []
            header = next(tsv_file).strip("\n").split("\t")
            self.assertEqual(header, COLUMNS, msg="header is not correct")
            for row, line in enumerate(tsv_file, start=2):
                with self.subTest(row=row, line=line):
                    line = line.strip("\n").split("\t")
                    self.assertEqual(
                        len(COLUMNS),
                        len(line),
                        msg="wrong number of columns. This is usually due to the wrong amount of trailing tabs.",
                    )
                    data = dict(zip(COLUMNS, line))
                    self.validate_row(data)
                    pubmeds.append(data["pubmed"])

            duplicated_pubmeds = sorted(
                pubmed for pubmed, count in Counter(pubmeds).items() if count > 1
            )
            if duplicated_pubmeds:
                kk = "\n".join(f"- {pubmed}" for pubmed in duplicated_pubmeds)
                self.fail(
                    msg=f"The following PubMed identifiers have multiple curations:\n\n{kk}\n\nI"
                    f"f you meant to overwrite an existing curation, delete the old row."
                )

            self.assertEqual(
                sorted(pubmeds),
                pubmeds,
                msg=f"""

    The curated papers in src/bioregistry/data/{CURATED_PAPERS_PATH.name}
    were not sorted properly.

    Please lint these files using the following commands in the console:

    $ pip install tox
    $ tox -e bioregistry-lint
            """,
            )
