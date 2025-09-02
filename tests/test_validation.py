"""Test for validation utilities."""

import unittest

import bioregistry
from bioregistry.validate.utils import Message, validate_jsonld

TEST_CONTEXT = {
    "@context": {
        "GO": "https://purl.obolibrary.org/obo/GO_",
        "nope": "https://example.org/nope/",
    }
}


class TestValidation(unittest.TestCase):
    """Test case for validation utilities."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rpm = bioregistry.manager.get_reverse_prefix_map()

    def test_validate_jsonld_exceptions(self) -> None:
        """Test errors when validating JSON-LD."""
        with self.assertRaises(TypeError):
            validate_jsonld(None)
        with self.assertRaises(TypeError):
            validate_jsonld({})
        with self.assertRaises(TypeError):
            validate_jsonld({"@context": None})

    def test_validate_jsonld(self) -> None:
        """Test validating JSON-LD."""
        messages = validate_jsonld(TEST_CONTEXT, strict=True, rpm=self.rpm)
        self.assert_messages_equal(
            [
                Message(
                    prefix="GO",
                    uri_prefix="https://purl.obolibrary.org/obo/GO_",
                    solution="Switch to standard prefix: go",
                    error="non-standard CURIE prefix",
                    level="error",
                ),
                Message(
                    prefix="nope",
                    uri_prefix="https://example.org/nope/",
                    error="unknown CURIE prefix",
                    level="error",
                ),
            ],
            messages,
        )

    def test_json_ld_non_strict(self) -> None:
        """Test non-strict validation of JSON-LD."""
        messages = validate_jsonld(TEST_CONTEXT, strict=False, rpm=self.rpm)
        self.assert_messages_equal(
            [
                Message(
                    prefix="GO",
                    uri_prefix="https://purl.obolibrary.org/obo/GO_",
                    solution="Switch to standard prefix: go",
                    error="non-standard CURIE prefix",
                    level="warning",
                ),
                Message(
                    prefix="nope",
                    uri_prefix="https://example.org/nope/",
                    error="unknown CURIE prefix",
                    level="error",
                ),
            ],
            messages,
        )

    def assert_messages_equal(self, expected: list[Message], actual: list[Message]) -> None:
        self.assertEqual(
            [m.model_dump() for m in expected],
            [m.model_dump() for m in actual],
        )

    def test_validate_ttl(self) -> None:
        """Test validation of turtle."""
