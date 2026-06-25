"""Direct tests for the data structure."""

import unittest

from bioregistry import Resource
from bioregistry.schema.record_accumulator import get_converter


class StructTest(unittest.TestCase):
    """Tests for the data structure."""

    def test_get_uri_prefix(self) -> None:
        """Test getting URI prefix."""
        # for a resource with no URI format, normally this will be false,
        # except when put in compatibility mode
        resource = Resource(prefix="test")
        self.assertIsNone(resource.get_uri_prefix())
        self.assertEqual("https://bioregistry.io/test:", resource.get_uri_prefix(stubs=True))

        resource = Resource(prefix="test", uri_format="https://example.com/$1")
        self.assertEqual("https://example.com/", resource.get_uri_prefix())

        resource = Resource(prefix="test", uri_format="https://example.com/$1.html")
        self.assertEqual("https://bioregistry.io/test:", resource.get_uri_prefix())

    def test_get_ols_uri_prefix(self) -> None:
        """Test getting OLS URI prefix."""
        internal_prefix = "test"
        external_prefix = "tset"
        rdf_uri_prefix = "https://example.com/test/"
        rdf_uri_format = f"{rdf_uri_prefix}$1"

        resource = Resource(prefix=internal_prefix)
        self.assertIsNone(resource.get_ols_uri_prefix())

        resource = Resource(
            prefix=internal_prefix,
            mappings={"ols": external_prefix},
            rdf_uri_format=rdf_uri_format,
        )
        self.assertEqual(external_prefix, resource.get_ols_prefix())
        self.assertEqual(
            f"https://www.ebi.ac.uk/ols/ontologies/{external_prefix}/terms?iri={rdf_uri_prefix}",
            resource.get_ols_uri_prefix(),
        )
        self.assertEqual(
            f"https://www.ebi.ac.uk/ols/ontologies/{external_prefix}/terms?iri={rdf_uri_prefix}0000001",
            resource.get_ols_iri("0000001"),
        )

        # test shortcut for obofoundry
        resource = Resource(
            prefix=internal_prefix,
            mappings={"ols": external_prefix, "obofoundry": external_prefix},
            obofoundry={"prefix": external_prefix},
        )
        self.assertEqual(external_prefix, resource.get_ols_prefix())
        self.assertEqual(
            f"https://www.ebi.ac.uk/ols/ontologies/{external_prefix}/terms?iri=http://purl.obolibrary.org/obo/{external_prefix.upper()}_",
            resource.get_ols_uri_prefix(),
        )

    def test_get_bioportal(self) -> None:
        """Test getting OLS URI prefix."""
        internal_prefix = "test"
        external_prefix = "tset"
        rdf_uri_prefix = "https://example.com/test/"
        rdf_uri_format = f"{rdf_uri_prefix}$1"

        resource = Resource(
            prefix=internal_prefix,
            mappings={"bioportal": external_prefix},
            rdf_uri_format=rdf_uri_format,
        )
        self.assertEqual(
            f"https://bioportal.bioontology.org/ontologies/{external_prefix}/?p=classes&conceptid={rdf_uri_prefix}0000001",
            resource.get_bioportal_iri("0000001"),
        )

    def test_record_accumulator(self) -> None:
        """Test record accumulator."""
        resource = Resource(prefix="test")

        converter = get_converter([resource])
        self.assertEqual({}, converter.bimap)

        converter = get_converter([resource], stubs=True)
        self.assertEqual({"test": "https://bioregistry.io/test:"}, converter.bimap)

        resource = Resource(prefix="test", uri_format="https://example.com/$1")
        converter = get_converter([resource])
        self.assertEqual({"test": "https://example.com/"}, converter.bimap)

        resource = Resource(prefix="test", uri_format="https://example.com/$1.html")
        converter = get_converter([resource])
        self.assertEqual({"test": "https://bioregistry.io/test:"}, converter.bimap)
