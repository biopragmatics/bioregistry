# -*- coding: utf-8 -*-

"""Tests for the metaregistry."""

import unittest

import bioregistry
from bioregistry.export.rdf_export import metaresource_to_rdf_str
from bioregistry.schema import Registry


class TestMetaregistry(unittest.TestCase):
    """Tests for the metaregistry."""

    def test_minimum_metadata(self):
        """Test the metaregistry entries have a minimum amount of data."""
        for metaprefix, registry_pydantic in bioregistry.read_metaregistry().items():
            self.assertIsInstance(registry_pydantic, Registry)
            data = registry_pydantic.dict()
            with self.subTest(metaprefix=metaprefix):
                self.assertIn("name", data)
                self.assertIn("homepage", data)
                self.assertIn("example", data)
                self.assertIn("description", data)

                # When a registry is a provider, it means it
                # provides for its entries
                self.assertIn("provider", data)
                if data["provider"]:
                    self.assertIn("provider_url", data)
                    self.assertIn("$1", data["provider_url"])

                # When a registry is a resolver, it means it
                # can resolve entries (prefixes) + identifiers
                self.assertIn("resolver", data)
                if data["resolver"]:
                    self.assertIn("resolver_url", data)
                    self.assertIn("$1", data["resolver_url"])
                    self.assertIn("$2", data["resolver_url"])

                invalid_keys = set(data).difference(
                    {
                        "prefix",
                        "name",
                        "homepage",
                        "download",
                        "provider",
                        "resolver",
                        "description",
                        "provider_url",
                        "example",
                        "resolver_url",
                        "contact",
                    }
                )
                self.assertEqual(set(), invalid_keys, msg="invalid metadata")

    def test_get_registry(self):
        """Test getting a registry."""
        self.assertIsNone(bioregistry.get_registry("nope"))
        self.assertIsNone(bioregistry.get_registry_name("nope"))
        self.assertIsNone(bioregistry.get_registry_homepage("nope"))
        self.assertIsNone(bioregistry.get_registry_url("nope", ...))
        self.assertIsNone(bioregistry.get_registry_example("nope"))
        self.assertIsNone(bioregistry.get_registry_description("nope"))
        self.assertIsNone(
            bioregistry.get_registry_url("n2t", ...)
        )  # no provider available for N2T registry

        metaprefix = "uniprot"
        registry = bioregistry.get_registry(metaprefix)
        self.assertIsInstance(registry, Registry)
        self.assertEqual(metaprefix, registry.prefix)

        self.assertEqual(registry.description, bioregistry.get_registry_description(metaprefix))

        homepage = "https://www.uniprot.org/database/"
        self.assertEqual(homepage, registry.homepage)
        self.assertEqual(homepage, bioregistry.get_registry_homepage(metaprefix))

        name = "UniProt Cross-ref database"
        self.assertEqual(name, registry.name)
        self.assertEqual(name, bioregistry.get_registry_name(metaprefix))

        example = "0174"
        self.assertEqual(example, registry.example)
        self.assertEqual(example, bioregistry.get_registry_example(metaprefix))

        url = bioregistry.get_registry_url(metaprefix, example)
        self.assertEqual("https://www.uniprot.org/database/DB-0174", url)

    def test_resolver(self):
        """Test generating resolver URLs."""
        # Can't resolve since nope isn't a valid registry
        self.assertIsNone(bioregistry.get_registry_resolve_url("nope", "chebi", "1234"))
        # Can't resolve since GO isn't a resolver
        self.assertIsNone(bioregistry.get_registry_resolve_url("go", "chebi", "1234"))

        url = bioregistry.get_registry_resolve_url("bioregistry", "chebi", "1234")
        self.assertEqual("https://bioregistry.io/chebi:1234", url)

    def test_get_rdf(self):
        """Test conversion to RDF."""
        s = metaresource_to_rdf_str("uniprot")
        self.assertIsInstance(s, str)
