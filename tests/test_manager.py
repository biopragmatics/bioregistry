# -*- coding: utf-8 -*-

"""Tests for managers."""

import unittest

import bioregistry
from bioregistry import Manager


class TestResourceManager(unittest.TestCase):
    """Test the registry manager."""

    def setUp(self) -> None:
        """Set up the test case with a resource manager."""
        self.manager = Manager()

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

    def test_rasterized_manager(self):
        """Test that generating a rasterized manager works the same for all functions."""
        rasterized_registry = self.manager._rasterized_registry()
        self.assertEqual(set(self.manager.registry), set(rasterized_registry))
        rast_manager = Manager(rasterized_registry)
        self.assertEqual(set(self.manager.registry), set(rast_manager.registry))
        self.assertEqual(self.manager.synonyms, rast_manager.synonyms)
        for prefix in self.manager.registry:
            with self.subTest(prefix=prefix):
                self.assertEqual(
                    self.manager.is_deprecated(prefix),
                    rast_manager.is_deprecated(prefix),
                )
                self.assertEqual(
                    self.manager.get_example(prefix),
                    rast_manager.get_example(prefix),
                )
                self.assertEqual(
                    self.manager.get_uri_format(prefix),
                    rast_manager.get_uri_format(prefix),
                )
                self.assertEqual(
                    self.manager.get_name(prefix),
                    rast_manager.get_name(prefix),
                )
                self.assertEqual(
                    self.manager.get_pattern(prefix),
                    rast_manager.get_pattern(prefix),
                )
                self.assertEqual(
                    self.manager.get_preferred_prefix(prefix) or prefix,
                    rast_manager.get_preferred_prefix(prefix),
                )
                self.assertEqual(
                    self.manager.get_synonyms(prefix),
                    rast_manager.get_synonyms(prefix),
                )
                self.assertEqual(
                    self.manager.get_depends_on(prefix),
                    rast_manager.get_depends_on(prefix),
                )
                self.assertEqual(
                    self.manager.get_appears_in(prefix),
                    rast_manager.get_appears_in(prefix),
                )
                self.assertEqual(
                    self.manager.get_provides_for(prefix),
                    rast_manager.get_provides_for(prefix),
                )
                self.assertEqual(
                    self.manager.get_provided_by(prefix),
                    rast_manager.get_provided_by(prefix),
                )
                self.assertEqual(
                    self.manager.get_has_canonical(prefix),
                    rast_manager.get_has_canonical(prefix),
                )
                self.assertEqual(
                    self.manager.get_canonical_for(prefix),
                    rast_manager.get_canonical_for(prefix),
                )
                self.assertEqual(
                    self.manager.get_part_of(prefix),
                    rast_manager.get_part_of(prefix),
                )
                self.assertEqual(
                    self.manager.get_has_parts(prefix),
                    rast_manager.get_has_parts(prefix),
                )
