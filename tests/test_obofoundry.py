# -*- coding: utf-8 -*-

"""Tests for OBO Foundry data."""

import unittest

from bioregistry import get_obofoundry_prefix


class TestOBO(unittest.TestCase):
    """Tests for OBO Foundry data."""

    def test_prefix(self):
        """Test looking up stylized prefixes."""
        for expected, query in [
            ("FBbt", "fbbt"),
            ("CHEBI", "chebi"),
        ]:
            with self.subTest(query=query):
                self.assertEqual(expected, get_obofoundry_prefix(query))
