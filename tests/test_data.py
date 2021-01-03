# -*- coding: utf-8 -*-

"""Tests for data integrity."""

import unittest

import bioregistry


class TestDuplicates(unittest.TestCase):
    """Tests for duplicates."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.registry = bioregistry.read_bioregistry()

    def test_names(self):
        """Test that all entries have a name."""
        for prefix, entry in self.registry.items():
            with self.subTest(prefix=prefix):
                self.assertFalse(
                    'name' not in entry
                    and 'name' not in entry.get('miriam', {})
                    and 'name' not in entry.get('ols', {})
                    and 'name' not in entry.get('obofoundry', {}),
                    msg=f'{prefix} is missing a name',
                )

    def test_patterns(self):
        """Test that all prefixes are norm-unique."""
        for prefix, entry in self.registry.items():
            pattern = entry.get('pattern')
            if pattern is None:
                continue
            with self.subTest(prefix=prefix):
                self.assertTrue(pattern.startswith('^'), msg=f'{prefix} pattern {pattern} should start with ^')
                self.assertTrue(pattern.endswith('$'), msg=f'{prefix} pattern {pattern} should end with $')

                # Check that it's the same as external definitions
                for key in ('miriam', 'wikidata'):
                    external_pattern = entry.get('key', {}).get('pattern')
                    if external_pattern:
                        self.assertEqual(pattern, external_pattern, msg=f'{prefix}: {key} pattern not same')
