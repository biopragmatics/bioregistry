# -*- coding: utf-8 -*-

"""Tests for OBO Foundry data."""

import unittest

from bioregistry import get_obofoundry_prefix


class TestOBO(unittest.TestCase):
    """Tests for OBO Foundry data."""

    def test_prefix(self):
        """Test looking up stylized prefixes."""
        self.assertEqual('FBbt', get_obofoundry_prefix('fbbt'))
        self.assertEqual('CHEBI', get_obofoundry_prefix('chebi'))
