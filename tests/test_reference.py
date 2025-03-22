"""Test references.

Run with

"""

import unittest

import curies
from pydantic import ValidationError

from bioregistry.reference import StandardReference, StandardNamedReference, StandardNamableReference

TEST_LUID = "0032571"
TEST_NAME = "response to vitamin K"
TEST_CURIES = ["go:0032571", "GO:0032571", "GO:GO:0032571"]
BAD_CURIES = [
    "nope:nope",  # fails because of missing prefix
    "go:0032571  asga",  # fails because of space
    "go:32571",  # failes because doesn't pass regex
]


class TestReference(unittest.TestCase):
    """Test references."""

    def test_failed_validation(self) -> None:
        """Test throwing a runtime error when missing prefix/identifier."""
        with self.assertRaises(RuntimeError):
            StandardReference.model_validate({})
        with self.assertRaises(RuntimeError):
            StandardReference.model_validate({"prefix": "nope"})
        with self.assertRaises(RuntimeError):
            StandardReference.model_validate({"identifier": "nope"})
        with self.assertRaises(RuntimeError):
            StandardReference.model_validate({"curie": "nope"})

    def test_invalid(self) -> None:
        """Test invalid CURIEs."""
        for curie in BAD_CURIES:
            for cls in [StandardReference, StandardNamableReference]:
                with self.subTest(curie=curie, cls=cls.__name__), self.assertRaises(ValidationError):
                    cls.from_curie(curie)

            with self.assertRaises(ValidationError):
                StandardNamedReference.from_curie(curie, name="something")

    def test_standard_reference(self) -> None:
        """Test parsing a regular reference."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                r1 = StandardReference.from_curie(curie)
                self.assertIsInstance(r1, StandardReference)
                self.assertEqual("go", r1.prefix)
                self.assertEqual(TEST_LUID, r1.identifier)
                self.assertFalse(hasattr(r1, "name"))

    def test_nameable_reference_no_name(self) -> None:
        """Test parsing namable reference without a name."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                r2 = StandardNamableReference.from_curie(curie)
                self.assertIsInstance(r2, curies.Reference)
                self.assertIsInstance(r2, curies.NamableReference)
                self.assertIsInstance(r2, StandardReference)
                self.assertIsInstance(r2, StandardNamableReference)
                self.assertEqual("go", r2.prefix)
                self.assertEqual(TEST_LUID, r2.identifier)
                self.assertTrue(hasattr(r2, "name"))
                self.assertIsNone(r2.name)

    def test_nameable_reference_with_name(self) -> None:
        """Test parsing namable reference with a name."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                r3 = StandardNamableReference.from_curie(curie, TEST_NAME)
                self.assertIsInstance(r3, curies.Reference)
                self.assertIsInstance(r3, curies.NamableReference)
                self.assertIsInstance(r3, StandardReference)
                self.assertIsInstance(r3, StandardNamableReference)
                self.assertEqual("go", r3.prefix)
                self.assertEqual(TEST_LUID, r3.identifier)
                self.assertTrue(hasattr(r3, "name"))
                self.assertIsNotNone(r3.name)
                self.assertEqual(TEST_NAME, r3.name)

    def test_named_reference(self) -> None:
        """Test parsing named references."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                r4 = StandardNamedReference.from_curie(curie, TEST_NAME)
                self.assertIsInstance(r4, curies.Reference)
                self.assertIsInstance(r4, curies.NamableReference)
                self.assertIsInstance(r4, curies.NamedReference)
                self.assertIsInstance(r4, StandardReference)
                self.assertIsInstance(r4, StandardNamableReference)
                self.assertIsInstance(r4, StandardNamedReference)
                self.assertEqual("go", r4.prefix)
                self.assertEqual(TEST_LUID, r4.identifier)
                self.assertTrue(hasattr(r4, "name"))
                self.assertEqual(TEST_NAME, r4.name)

    def test_equal(self) -> None:
        """Test equality between references."""
        r1 = curies.Reference(prefix="go", identifier=TEST_LUID)
        r2 = StandardNamedReference.from_curie(f"go:{TEST_LUID}", name=TEST_NAME)
        self.assertEqual(r1, r2)
