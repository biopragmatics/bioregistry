"""Tests for pandas utilities."""

import unittest

import pandas as pd

import bioregistry.pandas as brpd


class TestPandasUtils(unittest.TestCase):
    """Tests for pandas utilities."""

    def test_normalize_prefixes(self):
        """Test normalizing prefixes."""
        rows = [("go", "0000001"), ("GO", "0000001"), ("nopenope", "0000001")]
        columns = ["prefix", "identifier"]
        df = pd.DataFrame(rows, columns=columns)
        brpd.normalize_prefixes(df, "prefix")
        self.assertEqual(["go", "go", None], list(df["prefix"]))
