"""Test utilities."""

import unittest

from bioregistry.utils import backfill, deduplicate


class TestDeduplicate(unittest.TestCase):
    """Test deduplication workflow."""

    def test_backfill(self):
        """Test record backfill."""
        records = [
            {"pubmed": "pmid_1"},
            {"arxiv": "arxiv_1", "doi": "doi_1"},
            {"doi": "doi_1", "pubmed": "pmid_1", "title": "yup"},
            {"pubmed": "pmid_1"},
        ]
        res = backfill(records, keys=["pubmed", "doi", "pmc", "arxiv"])
        self.assertEqual(
            [
                {
                    "arxiv": "arxiv_1",
                    "doi": "doi_1",
                    "pubmed": "pmid_1",
                },
                {
                    "arxiv": "arxiv_1",
                    "doi": "doi_1",
                    "pubmed": "pmid_1",
                },
                {
                    "arxiv": "arxiv_1",
                    "doi": "doi_1",
                    "pubmed": "pmid_1",
                    "title": "yup",
                },
                {
                    "arxiv": "arxiv_1",
                    "doi": "doi_1",
                    "pubmed": "pmid_1",
                },
            ],
            res,
        )

    def test_deduplicate(self):
        """Test record deduplication."""
        records = [
            {"arxiv": "arxiv_1", "doi": "doi_1"},
            {"doi": "doi_1", "pubmed": "pmid_1", "title": "yup"},
            {"pubmed": "pmid_1", "pmc": "pmc_1"},
            {"pubmed": "pmid_1"},
        ]
        res = deduplicate(records, keys=["pubmed", "doi", "pmc", "arxiv"])
        self.assertEqual(
            [
                {
                    "arxiv": "arxiv_1",
                    "doi": "doi_1",
                    "pubmed": "pmid_1",
                    "title": "yup",
                    "pmc": "pmc_1",
                },
            ],
            res,
        )
