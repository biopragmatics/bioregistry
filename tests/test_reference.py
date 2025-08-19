"""Test references."""

import unittest

import curies
from pydantic import BaseModel, ValidationError

from bioregistry.reference import (
    NormalizedNamableReference,
    NormalizedNamedReference,
    NormalizedReference,
    StandardNamableReference,
    StandardNamedReference,
    StandardReference,
)

TEST_NORM_PREFIX = "go"
TEST_STANDARD_PREFIX = "GO"
TEST_LUID = "0032571"
TEST_NAME = "response to vitamin K"
TEST_CURIES = ["go:0032571", "GO:0032571", "GO:GO:0032571"]
BAD_CURIES = [
    "nope:nope",  # fails because of missing prefix
    "go:0032571  asga",  # fails because of space
    "go:32571",  # fails because doesn't pass regex
]


class TestNormalizedReference(unittest.TestCase):
    """Test normalized references, which use Bioregistry lowercasing."""

    def test_failed_validation(self) -> None:
        """Test throwing a runtime error when missing prefix/identifier."""
        for cls in [
            NormalizedReference,
            NormalizedNamableReference,
            StandardReference,
            StandardNamableReference,
            StandardNamedReference,
            NormalizedNamedReference,
        ]:
            with self.subTest(cls=cls.__name__):
                with self.assertRaises(RuntimeError):
                    cls.model_validate({})
                with self.assertRaises(RuntimeError):
                    cls.model_validate({"prefix": "nope"})
                with self.assertRaises(RuntimeError):
                    cls.model_validate({"identifier": "nope"})
                with self.assertRaises(RuntimeError):
                    cls.model_validate({"curie": "nope"})

    def test_invalid(self) -> None:
        """Test invalid CURIEs."""
        for curie in BAD_CURIES:
            for cls in [
                NormalizedReference,
                NormalizedNamableReference,
                StandardReference,
                StandardNamableReference,
            ]:
                with (
                    self.subTest(curie=curie, cls=cls.__name__),
                    self.assertRaises(ValidationError),
                ):
                    cls.from_curie(curie)

            with self.assertRaises(ValidationError):
                NormalizedNamedReference.from_curie(curie, name="something")

            with self.assertRaises(ValidationError):
                StandardNamedReference.from_curie(curie, name="something")

    def test_normalized_reference(self) -> None:
        """Test parsing a regular reference."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                reference = NormalizedReference.from_curie(curie)
                self.assertIsInstance(reference, NormalizedReference)
                self.assertEqual(TEST_NORM_PREFIX, reference.prefix)
                self.assertEqual(TEST_LUID, reference.identifier)
                self.assertFalse(hasattr(reference, "name"))

    def test_normalized_nameable_reference_no_name(self) -> None:
        """Test parsing namable reference without a name."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                reference = NormalizedNamableReference.from_curie(curie)
                self.assertIsInstance(reference, curies.Reference)
                self.assertIsInstance(reference, curies.NamableReference)
                self.assertIsInstance(reference, NormalizedReference)
                self.assertIsInstance(reference, NormalizedNamableReference)
                self.assertEqual(TEST_NORM_PREFIX, reference.prefix)
                self.assertEqual(TEST_LUID, reference.identifier)
                self.assertTrue(hasattr(reference, "name"))
                self.assertIsNone(reference.name)

    def test_normalized_nameable_reference_with_name(self) -> None:
        """Test parsing namable reference with a name."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                reference = NormalizedNamableReference.from_curie(curie, TEST_NAME)
                self.assertIsInstance(reference, curies.Reference)
                self.assertIsInstance(reference, curies.NamableReference)
                self.assertIsInstance(reference, NormalizedReference)
                self.assertIsInstance(reference, NormalizedNamableReference)
                self.assertEqual(TEST_NORM_PREFIX, reference.prefix)
                self.assertEqual(TEST_LUID, reference.identifier)
                self.assertTrue(hasattr(reference, "name"))
                self.assertEqual(TEST_NAME, reference.name)

    def test_normalized_named_reference(self) -> None:
        """Test parsing named references."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                reference = NormalizedNamedReference.from_curie(curie, TEST_NAME)
                self.assertIsInstance(reference, curies.Reference)
                self.assertIsInstance(reference, curies.NamableReference)
                self.assertIsInstance(reference, curies.NamedReference)
                self.assertIsInstance(reference, NormalizedReference)
                self.assertIsInstance(reference, NormalizedNamableReference)
                self.assertIsInstance(reference, NormalizedNamedReference)
                self.assertEqual(TEST_NORM_PREFIX, reference.prefix)
                self.assertEqual(TEST_LUID, reference.identifier)
                self.assertTrue(hasattr(reference, "name"))
                self.assertEqual(TEST_NAME, reference.name)

    def test_normalized_equal(self) -> None:
        """Test equality between references."""
        r1 = curies.Reference(prefix=TEST_NORM_PREFIX, identifier=TEST_LUID)
        r2 = NormalizedNamedReference.from_curie(f"go:{TEST_LUID}", name=TEST_NAME)
        r3 = curies.Reference(prefix=TEST_STANDARD_PREFIX, identifier=TEST_LUID)
        r4 = StandardNamedReference.from_curie(f"go:{TEST_LUID}", name=TEST_NAME)

        self.assertEqual(r1, r2)
        self.assertEqual(r3, r4)
        self.assertNotEqual(r1, r3)
        self.assertNotEqual(r1, r4)
        self.assertNotEqual(r2, r3)
        self.assertNotEqual(r2, r4)

    def test_derived_with_normalized(self) -> None:
        """Test derived."""

        class DerivedWithNormalizedReference(BaseModel):
            """A derived class with a normalized reference."""

            reference: NormalizedReference

        derived = DerivedWithNormalizedReference(reference="GO:0032571")
        self.assertEqual("go", derived.reference.prefix)
        self.assertEqual("0032571", derived.reference.identifier)


class TestStandardizeReference(unittest.TestCase):
    """Test standardized references, which use preferred prefixes."""

    def test_standard_reference(self) -> None:
        """Test parsing a regular reference."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                r1 = StandardReference.from_curie(curie)
                self.assertIsInstance(r1, StandardReference)
                self.assertEqual(TEST_STANDARD_PREFIX, r1.prefix)
                self.assertEqual(TEST_LUID, r1.identifier)
                self.assertFalse(hasattr(r1, "name"))

    def test_standard_nameable_reference_no_name(self) -> None:
        """Test parsing namable reference without a name."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                r2 = StandardNamableReference.from_curie(curie)
                self.assertIsInstance(r2, curies.Reference)
                self.assertIsInstance(r2, curies.NamableReference)
                self.assertIsInstance(r2, StandardReference)
                self.assertIsInstance(r2, StandardNamableReference)
                self.assertNotIsInstance(r2, NormalizedReference)
                self.assertNotIsInstance(r2, NormalizedNamableReference)
                self.assertEqual(TEST_STANDARD_PREFIX, r2.prefix)
                self.assertEqual(TEST_LUID, r2.identifier)
                self.assertTrue(hasattr(r2, "name"))
                self.assertIsNone(r2.name)

    def test_standard_nameable_reference_with_name(self) -> None:
        """Test parsing namable reference with a name."""
        for curie in TEST_CURIES:
            with self.subTest(curie=curie):
                r3 = StandardNamableReference.from_curie(curie, TEST_NAME)
                self.assertIsInstance(r3, curies.Reference)
                self.assertIsInstance(r3, curies.NamableReference)
                self.assertIsInstance(r3, StandardReference)
                self.assertIsInstance(r3, StandardNamableReference)
                self.assertNotIsInstance(r3, NormalizedReference)
                self.assertNotIsInstance(r3, NormalizedNamableReference)
                self.assertEqual(TEST_STANDARD_PREFIX, r3.prefix)
                self.assertEqual(TEST_LUID, r3.identifier)
                self.assertTrue(hasattr(r3, "name"))
                self.assertIsNotNone(r3.name)
                self.assertEqual(TEST_NAME, r3.name)

    def test_standard_named_reference(self) -> None:
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
                self.assertNotIsInstance(r4, NormalizedReference)
                self.assertNotIsInstance(r4, NormalizedNamableReference)
                self.assertNotIsInstance(r4, NormalizedNamedReference)
                self.assertEqual(TEST_STANDARD_PREFIX, r4.prefix)
                self.assertEqual(TEST_LUID, r4.identifier)
                self.assertTrue(hasattr(r4, "name"))
                self.assertEqual(TEST_NAME, r4.name)

    def test_derived_with_standard(self) -> None:
        """Test derived."""

        class DerivedWithStandardReference(BaseModel):
            """A derived class with a standard reference."""

            reference: StandardReference

        derived = DerivedWithStandardReference(reference="go:0032571")
        self.assertEqual("GO", derived.reference.prefix)
        self.assertEqual("0032571", derived.reference.identifier)
