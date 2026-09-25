"""Tests for the metaregistry."""

import unittest
from typing import ClassVar

import rdflib

import bioregistry
from bioregistry import Manager
from bioregistry.export.rdf_export import metaresource_to_rdf_str
from bioregistry.schema import Registry


class TestMetaregistry(unittest.TestCase):
    """Tests for the metaregistry."""

    manager: ClassVar[Manager]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test case."""
        cls.manager = Manager()

    def test_minimum_metadata(self) -> None:
        """Test the metaregistry entries have a minimum amount of data."""
        for metaprefix, registry in self.manager.metaregistry.items():
            self.assertIsInstance(registry, Registry)
            external_prefixes = set(
                self.manager.get_registry_invmap(metaprefix, use_obo_preferred=False)
            )
            with self.subTest(metaprefix=metaprefix):
                self.assertIsNotNone(registry.name)
                self.assertIsNotNone(registry.homepage)
                self.assertIsNotNone(registry.example)
                if metaprefix != "bioregistry" and external_prefixes:
                    self.assertIn(
                        registry.example,
                        external_prefixes,
                        msg="Examples should be external-registry specific and mapped",
                    )
                self.assertIsNotNone(registry.description)
                self.assertIsNotNone(registry.contact, msg="contact is None")
                self.assertNotEqual("FIXME", registry.contact.name)
                if "support" not in registry.contact.name.lower():
                    self.assertIsNotNone(registry.contact.orcid, msg="contact ORCiD is none")
                    self.assertIsNotNone(
                        registry.contact.github,
                        msg=f"missing github for {registry.prefix} for {registry.contact.name}",
                    )

                if registry.uri_format:
                    self.assertIsNotNone(registry.uri_format)
                    self.assertIn("$1", registry.uri_format)

                self.assertIsNotNone(registry.bioregistry_prefix)
                self.assertEqual(
                    bioregistry.normalize_prefix(registry.bioregistry_prefix),
                    registry.bioregistry_prefix,
                    msg="link from metaregistry to bioregistry must use canonical prefix",
                )
                resource = bioregistry.get_resource(registry.bioregistry_prefix)
                self.assertIsNotNone(resource)

                # When a registry is a resolver, it means it
                # can resolve entries (prefixes) + identifiers
                if registry.resolver_uri_format:
                    self.assertIn("$1", registry.resolver_uri_format)
                    self.assertIn("$2", registry.resolver_uri_format)
                    self.assertIsNotNone(registry.resolver_type)
                    self.assertIn(registry.resolver_type, {"lookup", "resolver"})

                invalid_keys = set(registry.model_dump()).difference(Registry.model_fields)
                self.assertEqual(set(), invalid_keys, msg="invalid metadata")

                if (
                    registry.governance is not None
                    and registry.governance.public_version_controlled_data
                ):
                    self.assertIsNotNone(registry.governance.data_repository)
                    self.assertIsNotNone(registry.governance.issue_tracker)

    def test_get_registry(self) -> None:
        """Test getting a registry."""
        self.assertIsNone(bioregistry.get_registry("nope"))
        self.assertIsNone(bioregistry.get_registry_name("nope"))
        self.assertIsNone(bioregistry.get_registry_homepage("nope"))
        self.assertIsNone(bioregistry.get_registry_provider_uri_format("nope", "nope"))
        self.assertIsNone(bioregistry.get_registry_example("nope"))
        self.assertIsNone(bioregistry.get_registry_description("nope"))

        metaprefix = "uniprot"
        registry = bioregistry.get_registry(metaprefix, strict=True)
        self.assertIsInstance(registry, Registry)
        self.assertEqual(metaprefix, registry.prefix)

        self.assertEqual(registry.description, bioregistry.get_registry_description(metaprefix))

        homepage = "https://www.uniprot.org/database"
        self.assertEqual(homepage, registry.homepage)
        self.assertEqual(homepage, bioregistry.get_registry_homepage(metaprefix))

        name = "UniProt Resource"
        self.assertEqual(name, registry.name)
        self.assertEqual(name, bioregistry.get_registry_name(metaprefix))

        example = "DB-0174"
        self.assertEqual(example, registry.example)
        self.assertEqual(example, bioregistry.get_registry_example(metaprefix))

        url = bioregistry.get_registry_provider_uri_format(metaprefix, example)
        self.assertEqual("https://www.uniprot.org/database/DB-0174", url)

    def test_resolver(self) -> None:
        """Test generating resolver URLs."""
        # Can't resolve since nope isn't a valid registry
        self.assertIsNone(bioregistry.get_registry_uri("nope", "chebi", "1234"))
        # Can't resolve since GO isn't a resolver
        self.assertIsNone(bioregistry.get_registry_uri("go", "chebi", "1234"))

        url = bioregistry.get_registry_uri("bioregistry", "chebi", "1234")
        self.assertEqual("https://bioregistry.io/chebi:1234", url)

    def test_get_rdf(self) -> None:
        """Test conversion to RDF."""
        registry = self.manager.metaregistry["uniprot"]
        s = metaresource_to_rdf_str(registry, manager=self.manager)
        self.assertIsInstance(s, str)
        g = rdflib.Graph()
        g.parse(data=s)

    def test_corresponding(self) -> None:
        """Test data corresponds between the registry and metaregistry."""
        for metaprefix, registry in self.manager.metaregistry.items():
            resource = self.manager.registry[registry.bioregistry_prefix]
            pattern = resource.get_pattern()
            if pattern is None:
                continue
            with self.subTest(metaprefix=metaprefix):
                self.assertRegex(registry.example, pattern)

                # Test URI format string
                if registry.uri_format:
                    uri_formats = resource.get_uri_formats()
                    self.assertLess(0, len(uri_formats))
                    self.assertIn(registry.uri_format, uri_formats)

                self.assertEqual(registry.contact, resource.get_contact())
                # self.assertEqual(registry.example, resource.get_example())
                self.assertEqual(registry.homepage, resource.get_homepage())
                self.assertEqual(registry.license, resource.get_license())
                self.assertEqual(registry.logo, resource.logo)
                self.assertEqual(registry.name, resource.get_name())
                self.assertEqual(registry.uri_format, resource.get_uri_format())
