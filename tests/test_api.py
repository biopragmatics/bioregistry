"""Tests for the top-level API functions."""

import unittest

import bioregistry


class TestAPI(unittest.TestCase):
    """Tests for top-level API functions."""

    def test_standardize_identifier(self):
        """Test standardizing identifiers."""
        config = [
            ("vario", "0376", "0376"),
            ("vario", "VariO:0376", "0376"),
            ("vario", "VariO_0376", "0376"),
            ("vario", "vario:0376", "0376"),
            ("vario", "VARIO:0376", "0376"),
            ("vario", "VARIO_0376", "0376"),
            ("swisslipid", "000000001", "000000001"),
            ("swisslipid", "SLM:000000001", "000000001"),
            ("fbbt", "00007294", "00007294"),
            ("chebi", "1234", "1234"),
            ("chebi", "CHEBI:1234", "1234"),
            ("chebi", "CHEBI_1234", "1234"),
            ("chebi", "chebi:1234", "1234"),
            ("chebi", "chebi_1234", "1234"),
            ("ncit", "C73192", "C73192"),
            ("ncbitaxon", "9606", "9606"),
            ("pdb", "00000020", "00000020"),
        ]
        for prefix, raw_id, standard_id in config:
            with self.subTest():
                self.assertEqual(
                    standard_id,
                    bioregistry.standardize_identifier(prefix, raw_id),
                )
