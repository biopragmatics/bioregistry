"""Tests for pandas utilities."""

import unittest

import pandas as pd

import bioregistry.pandas as brpd


class TestPandasUtils(unittest.TestCase):
    """Tests for pandas utilities."""

    def setUp(self) -> None:
        """Set up the test case."""
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
        """Test validating identifiers."""
        res = brpd.validate_identifiers(self.df, "identifier", prefix_column="prefix")
        self.assertEqual([True, True, False, False, None], list(res))

    @unittest.skip
    def test_normalize_identifiers(self):
        """Test normalizing identifiers."""
        brpd.normalize_identifiers(self.df)

        res = brpd.validate_identifiers(self.df, "identifier", prefix_column="prefix")
        # Note the fourth position got properly normalized and is True!
        self.assertEqual([True, True, False, True, None], list(res))

    def test_identifiers_to_curies(self):
        """Test converting local unique identifiers to CURIEs."""
        rows = [
            ("go", "0000001"),
            ("GO", "0000002"),
            ("xxx", "yyy"),
        ]
        columns = ["prefix", "identifier"]
        df = pd.DataFrame(rows, columns=columns)

        brpd.identifiers_to_curies(
            df, column="identifier", prefix_column="prefix", normalize_prefixes_=False
        )
        processed_rows = [
            ("go", "go:0000001"),
            ("GO", "GO:0000002"),
            ("xxx", "xxx:yyy"),
        ]
        self.assertEqual(processed_rows, [tuple(row) for row in df.values])

        df = pd.DataFrame(rows, columns=columns)
        brpd.identifiers_to_curies(
            df, column="identifier", prefix_column="prefix", normalize_prefixes_=True
        )
        processed_rows = [
            ("go", "go:0000001"),
            ("go", "go:0000002"),
            (None, None),
        ]
        self.assertEqual(processed_rows, [tuple(row) for row in df.values])

    def test_validate_curies(self):
        """Test validating CURIEs."""
        rows = [
            ("GO:0000001",),
            ("go:0000001",),
            ("nope:0000001",),
            ("go:GO:0000001",),
            ("go:go:0000001",),
            ("go:invalid",),
        ]
        columns = ["curie"]
        df = pd.DataFrame(rows, columns=columns)
        res = brpd.validate_curies(df, 0)
        self.assertEqual([False, True, False, False, False, False], list(res))
