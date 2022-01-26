# -*- coding: utf-8 -*-

"""Tests for downloading external data."""

import unittest

from bioregistry.external.obofoundry import get_obofoundry_example


class TestUtils(unittest.TestCase):
    """Test utilities."""

    def test_obolibrary_example(self):
        """Test looking up an example from the OBO Foundry PURL service configuration."""
        self.assertEqual("0011124", get_obofoundry_example("pcl"))
