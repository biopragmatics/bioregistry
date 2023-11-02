# -*- coding: utf-8 -*-

"""Test the ability of the bioregistry to cover INDRA identifiers."""

import unittest

import bioregistry

try:
    import indra
    import indra.databases.identifiers
except ImportError:
    indra = None

NON_BIOLOGY = {
    "UN",
    "WDI",
    "HUME",  # hume is a reading system
    "SOFIA",  # sofia is a reading system
    "CWMS",  # world modelers
}


@unittest.skipIf(indra is None, "INDRA not installed")
class TestIndra(unittest.TestCase):
    """Test the Bioregistry is a superset of INDRA identifier utilities."""

    def test_identifiers_mapping(self):
        """Test the identifier mappings are all contained in the Bioregistry."""
        for prefix, target in indra.databases.identifiers.identifiers_mappings.items():
            if prefix in {"CTD", "NONCODE", "NCBI"}:  # these aren't specific enough
                continue
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(
                    bioregistry.normalize_prefix(prefix), msg=f"should be {target}"
                )

    def test_non_registry(self):
        """Test the Bioregistry has entries for all non-registry entries in INDRA."""
        for prefix in indra.databases.identifiers.non_registry:
            if prefix == "SPINE":
                continue  # Special case due to a collaboration
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(bioregistry.normalize_prefix(prefix))

    def test_url_prefixes(self):
        """Test that all of the INDRA custom URL prefixes are mapped in the Bioregistry."""
        for prefix in indra.databases.identifiers.url_prefixes:
            if prefix in NON_BIOLOGY:
                continue
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(bioregistry.normalize_prefix(prefix))
