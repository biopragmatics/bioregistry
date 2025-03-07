"""Tests for identifiers.org."""

import unittest
from collections.abc import Mapping

import requests

import bioregistry
from bioregistry import (
    Resource,
    get_identifiers_org_curie,
    get_identifiers_org_iri,
    get_resource,
    manager,
)
from bioregistry.constants import IDOT_BROKEN, MIRIAM_BLACKLIST
from bioregistry.version import VERSION


class TestIdentifiersOrg(unittest.TestCase):
    """Tests for identifiers.org."""

    def setUp(self) -> None:
        """Prepare a session that has a user agent."""
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": f"bioregistry/{VERSION}",
        }
        self.entries: Mapping[str, Resource] = {
            prefix: entry
            for prefix, entry in bioregistry.read_registry().items()
            if entry.get_miriam_prefix()
        }

    def test_get_prefix(self):
        """Test getting identifiers.org prefixes."""
        for prefix, miriam_prefix in [
            ("ncbitaxon", "taxonomy"),
            ("ec", "ec-code"),
        ]:
            with self.subTest(prefix=prefix):
                self.assertEqual(miriam_prefix, bioregistry.get_identifiers_org_prefix(prefix))

        # Test prefixes that don't exist in MIRIAM
        for prefix in ["IDOMAL"]:
            self.assertIsNone(bioregistry.get_identifiers_org_prefix(prefix))

    def test_standardize_identifier(self):
        """Test that standardization makes patterns valid."""
        for prefix, entry in self.entries.items():
            if prefix in MIRIAM_BLACKLIST:
                continue
            example = entry.get_example()
            self.assertIsNotNone(example)
            pattern = entry.miriam.get("pattern")
            self.assertIsNotNone(pattern)
            with self.subTest(prefix=prefix, example=example, pattern=pattern):
                standardized_example = entry.miriam_standardize_identifier(example)
                self.assertIsNotNone(standardized_example)
                self.assertRegex(standardized_example, pattern)

    def test_curie(self):
        """Test CURIEs explicitly."""
        for prefix, identifier, expected in [
            # Standard
            ("pdb", "2gc4", "pdb:2gc4"),
            # Has namespace embedded in lui for pattern
            ("go", "0000001", "GO:0000001"),
            ("ark", "/12345/fk1234", "ark:/12345/fk1234"),
            # Require banana peels
            ("cellosaurus", "0001", "cellosaurus:CVCL_0001"),
            ("biomodels.kisao", "0000057", "biomodels.kisao:KISAO_0000057"),
            ("geogeo", "000000001", "geogeo:GEO_000000001"),
            ("geogeo", "000000001", "geogeo:GEO_000000001"),
            ("gramene.taxonomy", "013681", "gramene.taxonomy:GR_tax:013681"),
        ]:
            with self.subTest(prefix=prefix, identifier=identifier):
                self.assertEqual(expected, manager.get_miriam_curie(prefix, identifier))

    def test_url_banana(self):
        """Test that entries curated with a new banana are resolved properly."""
        for prefix, entry in self.entries.items():
            banana = entry.get_banana()
            if banana is None:
                continue
            if prefix in IDOT_BROKEN:
                continue  # identifiers.org is broken for these prefixes
            example = bioregistry.get_example(prefix)
            self.assertIsNotNone(example)
            with self.subTest(prefix=prefix, banana=banana, peel=entry.get_banana_peel()):
                self.assert_url(prefix, example)

    def assert_url(self, prefix: str, identifier: str):
        """Assert the URL resolves."""
        url = bioregistry.get_identifiers_org_iri(prefix, identifier)
        self.assertIsNotNone(url)
        res = self.session.get(url, allow_redirects=False)
        self.assertEqual(302, res.status_code, msg=f"failed with URL: {url}")

    @unittest.skip
    def test_url_auto(self):
        """Test generating and resolving Identifiers.org URIs.

        .. warning::

            This test takes up to 5 minutes since it makes a lot of web requests, and
            is therefore skipped by default.
        """
        for prefix, entry in self.entries.items():
            miriam_prefix = entry.get_identifiers_org_prefix()
            if miriam_prefix is None or prefix in IDOT_BROKEN:
                continue
            identifier = entry.get_example()
            with self.subTest(prefix=prefix, identifier=identifier):
                self.assert_url(prefix, identifier)

    def test_url(self):
        """Test formatting URLs."""
        for prefix, identifier, expected, _reason in [
            ("efo", "0000400", "efo:0000400", "test simple concatenation"),
            ("chebi", "CHEBI:1234", "CHEBI:1234", "test redundant namespace (standard)"),
            ("chebi", "1234", "CHEBI:1234", "test exclusion of redundant namespace (standard)"),
            (
                "mzspec",
                "PXD002255:ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2",
                "mzspec:PXD002255:ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2",
                "test simple concatenation with false banana",
            ),
            (
                "mzspec",
                "mzspec:PXD002255:ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2",
                "mzspec:PXD002255:ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2",
                "test simple concatenation (redundant) with false banana",
            ),
        ]:
            with self.subTest(p=prefix, i=identifier):
                curie = get_identifiers_org_curie(prefix, identifier)
                self.assertEqual(expected, curie, msg="wrong CURIE")

                url = get_identifiers_org_iri(prefix, identifier)
                self.assertEqual(f"https://identifiers.org/{curie}", url, msg="wrong URL")

                self.assert_url(prefix, identifier)

    def test_miriam_uri(self):
        """Test URI generation."""
        self.assertEqual(
            "https://identifiers.org/taxonomy:", get_resource("ncbitaxon").get_miriam_uri_prefix()
        )
        self.assertEqual("https://identifiers.org/GO:", get_resource("go").get_miriam_uri_prefix())
        self.assertEqual(
            "https://identifiers.org/doid/DOID:",
            get_resource("doid").get_miriam_uri_prefix(legacy_banana=True),
        )
        self.assertEqual(
            "https://identifiers.org/vario/VariO:",
            get_resource("vario").get_miriam_uri_prefix(legacy_banana=True),
        )
        self.assertEqual(
            "https://identifiers.org/cellosaurus/CVCL_",
            get_resource("cellosaurus").get_miriam_uri_prefix(legacy_banana=True),
        )
        self.assertEqual(
            "https://identifiers.org/DOID/",
            get_resource("doid").get_miriam_uri_prefix(legacy_delimiter=True),
        )
        self.assertIsNone(get_resource("sty").get_miriam_uri_prefix())
