"""Test utilities."""

import unittest

from bioregistry.utils import backfill, deduplicate, get_ec_url


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

    def test_ec_resolve(self) -> None:
        """Test resolving EC."""
        self.assertEqual(
            "https://www.enzyme-database.org/query.php?ec=1.2.3.4", get_ec_url("1.2.3.4")
        )
        self.assertEqual(
            "https://www.enzyme-database.org/class.php?c=1&sc=2&ssc=3", get_ec_url("1.2.3")
        )
        self.assertEqual(
            "https://www.enzyme-database.org/class.php?c=1&sc=2&ssc=3", get_ec_url("1.2.3.-")
        )
        self.assertEqual("https://www.enzyme-database.org/class.php?c=1&sc=2", get_ec_url("1.2"))
        self.assertEqual("https://www.enzyme-database.org/class.php?c=1&sc=2", get_ec_url("1.2.-"))
        self.assertEqual(
            "https://www.enzyme-database.org/class.php?c=1&sc=2", get_ec_url("1.2.-.-")
        )
        self.assertEqual("https://www.enzyme-database.org/class.php?c=1", get_ec_url("1"))
        self.assertEqual("https://www.enzyme-database.org/class.php?c=1", get_ec_url("1.-"))
        self.assertEqual("https://www.enzyme-database.org/class.php?c=1", get_ec_url("1.-.-"))
        self.assertEqual("https://www.enzyme-database.org/class.php?c=1", get_ec_url("1.-.-.-"))
