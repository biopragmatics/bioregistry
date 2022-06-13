"""Tests for pandas utilities."""

import unittest

import pandas as pd

import bioregistry.pandas as brpd


class TestPandasUtils(unittest.TestCase):
    """Tests for pandas utilities."""

    def setUp(self) -> None:
        self.rows = [
            ("go", "0000001"),
            ("GO", "0000001"),
            ("go", "invalid"),
            ("go", "GO:0000001"),
            ("nopenope", "0000001"),
        ]
        self.columns = ["prefix", "identifier"]
        self.df = pd.DataFrame(self.rows, columns=self.columns)

    def test_validate_prefixes(self):
        """Test normalizing prefixes."""
        for column in ["prefix", 0]:  # test both indexing techniques work
            res = brpd.validate_prefixes(self.df, column)
            self.assertEqual([True, False, True, True, False], list(res))

    def test_normalize_prefixes(self):
        """Test validating prefixes."""
        brpd.normalize_prefixes(self.df, "prefix")
        self.assertEqual(["go", "go", "go", "go", None], list(self.df["prefix"]))

        res = brpd.validate_prefixes(self.df, "prefix")
        self.assertEqual([True, True, True, True, None], list(res))

    def test_validate_identifiers(self):
        res = brpd.validate_identifiers(self.df, "identifier", prefix_column="prefix")
        self.assertEqual([True, True, False, False, None], list(res))

    @unittest.skip
    def test_normalize_identifiers(self):
        brpd.normalize_identifiers(self.df)

        res = brpd.validate_identifiers(self.df, "identifier", prefix_column="prefix")
        # Note the fourth position got properly normalized and is True!
        self.assertEqual([True, True, False, True, None], list(res))
