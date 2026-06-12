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
