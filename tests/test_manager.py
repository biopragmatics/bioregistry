# -*- coding: utf-8 -*-

"""Tests for managers."""

import unittest

import bioregistry
from bioregistry.resource_manager import ResourceManager


class TestResourceManager(unittest.TestCase):
    """Test the registry manager."""

    def setUp(self) -> None:
        """Set up the test case with a resource manager."""
        self.manager = ResourceManager()

    def test_prefix_map_preferred(self):
        """Test using preferred prefixes in the prefix map."""
        prefix_map = self.manager.get_prefix_map(
            priority=["obofoundry", "default"],
            use_preferred=True,
        )
        self.assertNotIn("fbbt", prefix_map)
        self.assertIn("FBbt", prefix_map)

        prefix_map = bioregistry.get_prefix_map(
            priority=["obofoundry", "default"],
            use_preferred=True,
        )
        self.assertNotIn("fbbt", prefix_map)
        self.assertIn("FBbt", prefix_map)
