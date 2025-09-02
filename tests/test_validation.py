"""Test for validation utilities."""

import unittest

from bioregistry.validate.utils import Message, validate_jsonld


class TestValidation(unittest.TestCase):
    """Test case for validation utilities."""

    def test_validate_jsonld(self):
        """Test validating JSON-LD."""
        with self.assertRaises(TypeError):
            validate_jsonld(None)
        with self.assertRaises(TypeError):
            validate_jsonld({})
        with self.assertRaises(TypeError):
            validate_jsonld({"@context": None})

        test_context = {
            "@context": {
                "GO": "https://purl.obolibrary.org/obo/GO_",
                "nope": "https://example.org/nope/",
            }
        }
        messages = validate_jsonld(test_context, strict=True)
        self.assertEqual(
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
                    error="invalid",
                    level="error",
                ),
            ],
            messages,
        )

        messages = validate_jsonld(test_context, strict=False)
        self.assertEqual(
            [
                Message(
                    prefix="GO",
                    uri_prefix="https://purl.obolibrary.org/obo/GO_",
                    solution="Switch to standard prefix: go",
                    error="nonstandard",
                    level="warning",
                ),
                Message(
                    prefix="nope",
                    uri_prefix="https://example.org/nope/",
                    error="invalid",
                    level="error",
                ),
            ],
            messages,
        )

    def test_validate_ttl(self) -> None:
        """Test validation of turtle."""
        raise NotImplementedError
