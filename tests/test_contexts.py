# -*- coding: utf-8 -*-

"""Tests for checking the integrity of the contexts."""

import json
import unittest

import bioregistry
from bioregistry.constants import CONTEXTS_PATH
from bioregistry.utils import extended_encoder


class TestContexts(unittest.TestCase):
    """A test case for checking the integrity of the contexts."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.contexts = bioregistry.read_contexts()
        self.valid_metaprefixes = set(bioregistry.read_metaregistry()) | {"default"}
        self.valid_prefixes = set(bioregistry.read_registry())

    def test_linted(self):
        """Test the context file is linted."""
        text = CONTEXTS_PATH.read_text(encoding="utf-8")
        linted_text = json.dumps(
            json.loads(text),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=extended_encoder,
        )
        self.assertEqual(linted_text, text)

    def test_data(self):
        """Test the data integrity."""
        for context in self.contexts.values():
            for maintainer in context.maintainers:
                self.assertIsNotNone(maintainer.name)
                # self.assertIsNotNone(maintainer.email, msg=f"{maintainer.name} is missing an email")
                self.assertIsNotNone(
                    maintainer.github, msg=f"{maintainer.name} is missing a GitHub handle"
                )
                self.assertIsNotNone(maintainer.orcid, msg=f"{maintainer.name} is missing an ORCID")
                self.assertRegex(maintainer.orcid, "^\\d{4}-\\d{4}-\\d{4}-\\d{3}(\\d|X)$")

            for metaprefix in context.uri_prefix_priority or []:
                self.assertIn(metaprefix, self.valid_metaprefixes)
            for metaprefix in context.prefix_priority or []:
                self.assertIn(metaprefix, self.valid_metaprefixes)
            for prefix in context.prefix_remapping or {}:
                self.assertIn(prefix, self.valid_prefixes)
