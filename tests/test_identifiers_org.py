# -*- coding: utf-8 -*-

"""Tests for identifiers.org."""

import unittest

import requests

from bioregistry import get_identifiers_org_curie, get_identifiers_org_url


class TestIdentifiersOrg(unittest.TestCase):
    """Tests for identifiers.org."""

    def test_url(self):
        """Test formatting URLs."""
        for prefix, identifier, expected, _reason in [
            ('efo', '0000400', 'efo:0000400', 'test simple concatenation'),
            ('chebi', 'CHEBI:1234', 'CHEBI:1234', 'test redundant namespace (standard)'),
            ('chebi', '1234', 'CHEBI:1234', 'test exclusion of redundant namespace (standard)'),
            (
                'mzspec',
                'PXD002255::ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2',
                'mzspec:PXD002255::ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2',
                'test simple concatenation with false banana',
            ),
            (
                'mzspec',
                'mzspec:PXD002255::ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2',
                'mzspec:PXD002255::ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2',
                'test simple concatenation (redundant) with false banana',
            ),
        ]:
            with self.subTest(p=prefix, i=identifier):
                curie = get_identifiers_org_curie(prefix, identifier)
                self.assertEqual(expected, curie, msg='wrong CURIE')

                url = get_identifiers_org_url(prefix, identifier)
                self.assertEqual(f'https://identifiers.org/{curie}', url, msg='wrong URL')

                # Check that the URL resolves
                res = requests.get(url)
                self.assertEqual(200, res.status_code, msg=res.reason)
