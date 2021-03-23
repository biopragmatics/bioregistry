# -*- coding: utf-8 -*-

"""Test the ability of the bioregsitry to cover INDRA identifiers."""

import unittest

import bioregistry

try:
    import indra
    import indra.databases.identifiers
except ImportError:
    indra = None

NON_BIOLOGY = {
    'UN', 'WDI', ' HUME',
}


@unittest.skipIf(indra is None, 'INDRA not installed')
class TestIndra(unittest.TestCase):
    def test_identifiers_mapping(self):
        for prefix, target in indra.databases.identifiers.identifiers_mappings.items():
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(bioregistry.normalize_prefix(prefix), msg=f'should be {target}')

    def test_non_registry(self):
        for prefix in indra.databases.identifiers.non_registry:
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(bioregistry.normalize_prefix(prefix))

    def test_url_prefixes(self):
        for prefix in indra.databases.identifiers.url_prefixes:
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(bioregistry.normalize_prefix(prefix))
