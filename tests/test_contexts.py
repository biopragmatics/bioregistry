"""Tests for checking the integrity of the contexts."""

import json
import unittest

import bioregistry
from bioregistry import Resource, manager
from bioregistry.constants import CONTEXTS_PATH


class TestContexts(unittest.TestCase):
    """A test case for checking the integrity of the contexts."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.contexts = bioregistry.read_contexts()
        self.collection_keys = {
            collection.context: key
            for key, collection in bioregistry.read_collections().items()
            if collection.context
        }
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
        )
        self.assertEqual(linted_text, text)

    def test_obo_context(self):
        """Test the OBO context map."""
        p = "http://purl.obolibrary.org/obo"
        prefix_map, pattern_map = manager.get_context_artifacts("obo", include_synonyms=False)

        self.assertIn("KISAO", prefix_map)
        self.assertEqual(f"{p}/KISAO_", prefix_map["KISAO"])
        self.assertIn("FBcv", prefix_map)
        self.assertEqual(f"{p}/FBcv_", prefix_map["FBcv"])
        self.assertIn("GEO", prefix_map)
        self.assertEqual(f"{p}/GEO_", prefix_map["GEO"])
        self.assertEqual("https://www.ncbi.nlm.nih.gov/pubmed/", prefix_map["PMID"])

        self.assertNotIn("biomodels.kisao", prefix_map)

        prefix_map, pattern_map = manager.get_context_artifacts("obo", include_synonyms=True)
        self.assertIn("KISAO", prefix_map)
        self.assertIn(
            "biomodels.kisao",
            prefix_map,
            msg="When overriding, this means that bioregistry prefix isn't properly added to the synonyms list",
        )

    def test_obo_converter(self):
        """Test getting a converter from a context."""
        converter = manager.get_converter_from_context("obo")
        self.assertEqual("ICD10WHO", converter.standardize_prefix("icd10"))
        self.assertEqual("Orphanet", converter.standardize_prefix("ordo"))
        self.assertEqual("GO", converter.standardize_prefix("GO"))
        self.assertEqual("GO", converter.standardize_prefix("gomf"))
        self.assertEqual("https://www.ncbi.nlm.nih.gov/pubmed/", converter.bimap["PMID"])
        self.assertEqual("GO", converter.standardize_prefix("go"))
        self.assertEqual("oboInOwl", converter.standardize_prefix("oboinowl"))

    def test_data(self):
        """Test the data integrity."""
        for key, context in self.contexts.items():
            self.assertNotIn(
                key,
                set(self.collection_keys),
                msg=f"Context has same key as context assigned by collection {self.collection_keys.get(key)}",
            )

            for maintainer in context.maintainers:
                self.assertIsNotNone(maintainer.name)
                # self.assertIsNotNone(maintainer.email, msg=f"{maintainer.name} is missing an email")
                self.assertIsNotNone(
                    maintainer.github, msg=f"{maintainer.name} is missing a GitHub handle"
                )
                self.assertIsNotNone(maintainer.orcid, msg=f"{maintainer.name} is missing an ORCID")
                self.assertRegex(maintainer.orcid, "^\\d{4}-\\d{4}-\\d{4}-\\d{3}(\\d|X)$")

            for metaprefix in context.uri_prefix_priority or []:
                self.assertIn(metaprefix, self.valid_metaprefixes.union(Resource.URI_FORMATTERS))
            for metaprefix in context.prefix_priority or []:
                self.assertIn(
                    metaprefix,
                    self.valid_metaprefixes.union({"obofoundry.preferred", "preferred", "default"}),
                )
            remapping = context.prefix_remapping or {}
            _valid_remapping_prefixes = set(
                bioregistry.get_prefix_map(
                    uri_prefix_priority=context.uri_prefix_priority,
                )
            )
            for prefix in remapping:
                # Currently this allows overwriting of existing prefixes
                self.assertIn(prefix, _valid_remapping_prefixes)

            _valid_custom_prefixes = set(
                bioregistry.get_prefix_map(
                    remapping=remapping,
                    uri_prefix_priority=context.uri_prefix_priority,
                )
            )
            invalid_custom_prefixes = {
                prefix
                for prefix in (context.custom_prefix_map or {})
                if prefix not in _valid_custom_prefixes
            }
            self.assertEqual(
                0,
                len(invalid_custom_prefixes),
                msg=f"""

    All prefixes in the custom prefix mapping should either be canonical prefixes or generated by the prefix remapping

    Invalid prefixes: {", ".join(sorted(invalid_custom_prefixes))}
""",
            )

            for blacklist_prefix in context.blacklist or []:
                self.assertIn(blacklist_prefix, self.valid_prefixes)
