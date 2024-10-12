# -*- coding: utf-8 -*-

"""Test for checking the integrity of the curated_papers TSV file."""

import csv
import unittest
from datetime import datetime

import bioregistry
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

        self.assertTrue(row["pmid"].isdigit(), msg="PubMed identifier should be an integer")
        self.assertTrue(row["pr_added"].isdigit(), msg="Pull Request should be an integer")

        # Validate relevant is 0 or 1
        self.assertIn(row["relevant"], ["0", "1"])

        if row["relevant"] == "1":
            prefix = row["prefix"]
            self.assertIsNotNone(prefix, msg="prefix should be set for all relevant entries")
            self.assertNotEqual("", prefix, msg="prefix should not be empty for relevant entries")
            self.assertEqual(
                bioregistry.normalize_prefix(prefix),
                prefix,
                msg="prefix should be standardized for relevant entries",
            )

        # Validate relevancy_type is in relevancy_vocab
        self.assertIn(row["relevancy_type"], self.relevancy_types)

        self.assertRegex(row["orcid"], ORCID_PATTERN)

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
            reader = csv.DictReader(tsv_file, delimiter="\t")
            for row, data in enumerate(reader, start=1):
                with self.subTest(row=row, data=data):
                    self.validate_row(data)
