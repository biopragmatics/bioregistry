# -*- coding: utf-8 -*-

"""Test for checking the integrity of the curated_papers TSV file."""

import csv
import re
import unittest
from datetime import datetime

from bioregistry.constants import (
    CURATED_PAPERS_PATH,
    CURATED_PAPERS_RELEVANCY_VOCAB,
    ORCID_PATTERN,
)


class TestTSV(unittest.TestCase):
    """Tests for curated_papers tsv file."""

    def setUp(self):
        """Set up the test case."""
        self.tsv_file_path = CURATED_PAPERS_PATH
        self.relevancy_vocab = CURATED_PAPERS_RELEVANCY_VOCAB
        self.orcid_pattern = re.compile(ORCID_PATTERN)

    def validate_row(self, row):
        """Validate a single row from the TSV file."""
        # Validate required fields
        required_fields = ["pmid", "relevant", "relevancy_type", "orcid", "date_curated"]
        for field in required_fields:
            self.assertIn(field, row)

        # Validate pmid is an integer
        self.assertTrue(row["pmid"].isdigit())

        # Validate relevant is 0 or 1
        self.assertIn(row["relevant"], ["0", "1"])

        # Validate relevancy_type is in relevancy_vocab
        self.assertIn(row["relevancy_type"], self.relevancy_vocab)

        # Validate orcid against oricd_pattern
        self.assertTrue(self.orcid_pattern.match(row["orcid"]))

        # Validate date_curated format
        try:
            datetime.strptime(row["date_curated"], "%Y-%m-%d")
        except ValueError:
            self.fail("Date_curated should follow format YYYY-MM-DD")

    def test_tsv_file(self):
        """Tests all rows in TSV file are valid."""
        with open(self.tsv_file_path, mode="r") as tsv_file:
            tsv_reader = csv.DictReader(tsv_file, delimiter="\t")
            for row in tsv_reader:
                with self.subTest(row=row):
                    self.validate_row(row)


if __name__ == "__main__":
    unittest.main()
