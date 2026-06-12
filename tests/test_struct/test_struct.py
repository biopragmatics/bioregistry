"""Direct tests for the data structure."""

import unittest

from bioregistry import Resource


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
