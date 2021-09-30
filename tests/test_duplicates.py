# -*- coding: utf-8 -*-

"""Tests to make sure there are no duplicates."""

import unittest

from more_itertools import pairwise

import bioregistry
from bioregistry.utils import norm


class TestDuplicates(unittest.TestCase):
    """Tests for duplicates."""

    def test_unique_keys(self):
        """Test that all prefixes are norm-unique."""
        registry = bioregistry.read_registry()

        for a, b in pairwise(sorted(registry, key=norm)):
            with self.subTest(a=a, b=b):
                self.assertNotEqual(norm(a), norm(b))

    def test_synonyms(self):
        """Test that there are no synonyms that conflict with keys."""
        registry = bioregistry.read_registry()
        norm_prefixes = {norm(prefix) for prefix in registry}

        for key, entry in registry.items():
            for synonym in entry.synonyms or []:
                with self.subTest(key=key, synonym=synonym):
                    self.assertNotIn(synonym, norm_prefixes - {norm(key)})
