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
                self.assertIsNotNone(registry_pydantic.contact)
                self.assertNotEqual("FIXME", registry_pydantic.contact.name)
                if "support" not in registry_pydantic.contact.name.lower():
                    self.assertIsNotNone(registry_pydantic.contact.orcid)
                    self.assertIsNotNone(registry_pydantic.contact.github)

                if registry_pydantic.provider_uri_format:
                    self.assertIn("provider_uri_format", data)
                    self.assertIn("$1", data["provider_uri_format"])

                if (
                    # Missing URI format string
                    not registry_pydantic.provider_uri_format
                    # Unresolved overlap in Bioregistry
                    or metaprefix in bioregistry.read_registry()
                    # Has URI format string, but not in proper form
                    or (
                        registry_pydantic.provider_uri_format
                        and not registry_pydantic.provider_uri_format.endswith("$1")
                    )
                ):
                    self.assertIsNotNone(registry_pydantic.bioregistry_prefix)

                if registry_pydantic.bioregistry_prefix:
                    self.assertEqual(
                        bioregistry.normalize_prefix(registry_pydantic.bioregistry_prefix),
                        registry_pydantic.bioregistry_prefix,
                        msg="link from metaregistry to bioregistry must use canonical prefix",
                    )
                    resource = bioregistry.get_resource(registry_pydantic.bioregistry_prefix)
                    self.assertIsNotNone(resource)
                    self.assertIsNotNone(
                        resource.get_uri_format(),
                        msg=f"corresponding registry entry ({registry_pydantic.bioregistry_prefix})"
                        f" is missing a uri_format",
                    )

                # When a registry is a resolver, it means it
                # can resolve entries (prefixes) + identifiers
                if registry_pydantic.resolver_uri_format:
                    self.assertIn("resolver_uri_format", data)
                    self.assertIn("$1", data["resolver_uri_format"])
                    self.assertIn("$2", data["resolver_uri_format"])
                    self.assertIsNotNone(registry_pydantic.resolver_type)
                    self.assertIn(data["resolver_type"], {"lookup", "resolver"})
                else:
                    self.assertIsNone(registry_pydantic.resolver_type)

                invalid_keys = set(data).difference(
                    {
                        "prefix",
                        "name",
                        "homepage",
                        "download",
                        "description",
                        "provider_uri_format",
                        "example",
                        "resolver_uri_format",
                        "resolver_type",
                        "contact",
                        "availability",
                        "bioregistry_prefix",
                    }
                )
                self.assertEqual(set(), invalid_keys, msg="invalid metadata")
                if not registry_pydantic.availability.fair:
                    self.assertIsNone(
                        registry_pydantic.download,
                        msg="If bulk download available, resource should be annotated as FAIR",
                    )
                    self.assertIsNotNone(
                        registry_pydantic.availability.fair_note,
                        msg="All non-FAIR resources require an explanation",
                    )

    def test_get_registry(self):
        """Test getting a registry."""
        self.assertIsNone(bioregistry.get_registry("nope"))
        self.assertIsNone(bioregistry.get_registry_name("nope"))
        self.assertIsNone(bioregistry.get_registry_homepage("nope"))
        self.assertIsNone(bioregistry.get_registry_provider_uri_format("nope", ...))
        self.assertIsNone(bioregistry.get_registry_example("nope"))
        self.assertIsNone(bioregistry.get_registry_description("nope"))

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

        url = bioregistry.get_registry_provider_uri_format(metaprefix, example)
        self.assertEqual("https://www.uniprot.org/database/DB-0174", url)

    def test_resolver(self):
        """Test generating resolver URLs."""
        # Can't resolve since nope isn't a valid registry
        self.assertIsNone(bioregistry.get_registry_uri("nope", "chebi", "1234"))
        # Can't resolve since GO isn't a resolver
        self.assertIsNone(bioregistry.get_registry_uri("go", "chebi", "1234"))

        url = bioregistry.get_registry_uri("bioregistry", "chebi", "1234")
        self.assertEqual("https://bioregistry.io/chebi:1234", url)

    def test_get_rdf(self):
        """Test conversion to RDF."""
        s = metaresource_to_rdf_str("uniprot")
        self.assertIsInstance(s, str)
