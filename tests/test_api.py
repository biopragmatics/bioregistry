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

    def test_default_converter(self) -> None:
        """Test the default converter."""
        c = bioregistry.get_default_converter()
        self.assertEqual(
            "kegg.pathway",
            c.standardize_prefix("kegg.pathway"),
        )
        self.assertEqual(
            "kegg.pathway:hsa00010",
            c.standardize_curie("kegg.pathway:hsa00010", strict=True),
            msg="kegg.pathway should have its own URI space and not get chunked into kegg",
        )
        self.assertEqual(
            "chmo",
            c.standardize_prefix("CHMO"),
            msg="preferred prefixes aren't making it through.",
        )
        self.assertEqual(
            "chmo:0000073",
            c.standardize_curie("CHMO:0000073"),
        )
        self.assertEqual(
            "http://purl.obolibrary.org/obo/CHMO_0000073",
            c.expand("CHMO:0000073"),
        )
