"""Tests for collections."""

import logging
import unittest
from collections import Counter

import rdflib

import bioregistry
from bioregistry import manager
from bioregistry.constants import NFDI_ROR
from bioregistry.export.rdf_export import collection_to_rdf_str
from bioregistry.schema import Collection
from bioregistry.schema_utils import _lint_collection_resources

logger = logging.getLogger(__name__)


class TestCollections(unittest.TestCase):
    """Tests for collections."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.manager = manager

    def test_minimum_metadata(self) -> None:
        """Check collections have minimal metadata and correct prefixes."""
        for key, collection in sorted(self.manager.collections.items()):
            with self.subTest(key=key):
                self.assertRegex(key, "^\\d{7}$")

                incorrect_msg = ""
                for prefix in collection.get_prefixes():
                    np = self.manager.normalize_prefix(prefix)
                    if np == prefix:
                        pass
                    elif np is None:
                        incorrect_msg += f"\n- {prefix} could not be looked up"
                    else:
                        incorrect_msg += f"\n- {prefix} should be standardized to {np}"
                if incorrect_msg:
                    self.fail(msg=f"in {key}, the following errors were found:\n{incorrect_msg}")

                duplicates = {
                    prefix
                    for prefix, count in Counter(collection.get_prefixes()).items()
                    if 1 < count
                }
                self.assertEqual(set(), duplicates, msg="Duplicates found")
                self.assertEqual(
                    _lint_collection_resources(collection.resources), collection.resources
                )

                for mapping in collection.mappings or []:
                    self.assertTrue(
                        bioregistry.is_valid_curie(mapping.curie),
                        msg=f"invalid mapping: {mapping.curie}",
                    )

    def test_get_collection(self) -> None:
        """Test getting a collection."""
        self.assertIsNone(self.manager.collections.get("nope"))

        identifier = "0000001"
        collection = self.manager.collections.get(identifier)
        if collection is None:
            raise self.fail(msg="No collection found")
        self.assertIsInstance(collection, Collection)
        self.assertEqual(identifier, collection.identifier)

        # Check building a prefix map
        prefix_map = collection.as_prefix_map()
        self.assertIsInstance(prefix_map, dict)

        # Check building a JSON-LD context.
        context_jsonld = collection.as_context_jsonld()
        self.assertIsInstance(context_jsonld, dict)
        self.assertIn("@context", context_jsonld)
        self.assertEqual(prefix_map, context_jsonld["@context"])

    def test_get_rdf(self) -> None:
        """Test conversion to RDF."""
        collection = manager.collections["0000001"]
        s = collection_to_rdf_str(collection, manager=self.manager)
        self.assertIsInstance(s, str)
        g = rdflib.Graph()
        g.parse(data=s)

    def test_nfdi(self) -> None:
        """Test NFDI collections."""
        for collection in self.manager.collections.values():
            if not collection.has_organization_with_ror(NFDI_ROR):
                continue
            with self.subTest(name=collection.name):
                self.assertIsNotNone(collection.logo, msg="all NFDI collections need a logo")
