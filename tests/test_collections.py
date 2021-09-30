# -*- coding: utf-8 -*-

"""Tests for collections."""

import logging
import unittest
from collections import Counter

import bioregistry
from bioregistry.export.rdf_export import collection_to_rdf_str
from bioregistry.schema import Collection

logger = logging.getLogger(__name__)


class TestCollections(unittest.TestCase):
    """Tests for collections."""

    def test_minimum_metadata(self):
        """Check collections have minimal metadata and correct prefixes."""
        registry = bioregistry.read_registry()

        for key, collection_pydantic in sorted(bioregistry.read_collections().items()):
            self.assertIsInstance(collection_pydantic, Collection)
            collection = collection_pydantic.dict()
            with self.subTest(key=key):
                self.assertRegex(key, "^\\d{7}$")
                self.assertIn("name", collection)
                self.assertIn("authors", collection)
                self.assertIsInstance(collection["authors"], list, msg=f"Collection: {collection}")
                for author in collection["authors"]:
                    self.assertIn("name", author)
                    self.assertIn("orcid", author)
                    self.assertRegex(author["orcid"], bioregistry.get_pattern("orcid"))
                self.assertIn("description", collection)
                incorrect = {prefix for prefix in collection["resources"] if prefix not in registry}
                self.assertEqual(set(), incorrect, msg="Invalid prefixes")
                duplicates = {
                    prefix
                    for prefix, count in Counter(collection["resources"]).items()
                    if 1 < count
                }
                self.assertEqual(set(), duplicates, msg="Duplicates found")

    def test_get_collection(self):
        """Test getting a collection."""
        self.assertIsNone(bioregistry.get_collection("nope"))

        identifier = "0000001"
        collection = bioregistry.get_collection(identifier)
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

    def test_get_rdf(self):
        """Test conversion to RDF."""
        s = collection_to_rdf_str("0000001")
        self.assertIsInstance(s, str)
