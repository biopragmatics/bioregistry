# -*- coding: utf-8 -*-

"""Tests for identifiers.org."""

import unittest
from textwrap import dedent, fill

import requests

import bioregistry
from bioregistry import get_identifiers_org_curie, get_identifiers_org_iri
from bioregistry.constants import IDOT_BROKEN
from bioregistry.version import VERSION


class TestIdentifiersOrg(unittest.TestCase):
    """Tests for identifiers.org."""

    def setUp(self) -> None:
        """Prepare a session that has a user agent."""
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": f"bioregistry/{VERSION}",
        }

    def test_get_prefix(self):
        """Test getting identifiers.org prefixes."""
        for prefix, miriam_prefix in [
            ("ncbitaxon", "taxonomy"),
            ("eccode", "ec-code"),
        ]:
            with self.subTest(prefix=prefix):
                self.assertEqual(miriam_prefix, bioregistry.get_identifiers_org_prefix(prefix))

        for prefix in ["MONDO"]:
            self.assertIsNone(bioregistry.get_identifiers_org_prefix(prefix))

    def test_banana(self):
        """Test that entries curated with a new banana are resolved properly."""
        for prefix, entry in bioregistry.read_registry().items():
            banana = entry.banana
            if banana is None:
                continue
            if prefix in IDOT_BROKEN:
                continue  # identifiers.org is broken for these prefixes
            with self.subTest(
                prefix=prefix,
                banana=banana,
                pattern=bioregistry.get_pattern(prefix),
            ):
                identifier = bioregistry.get_example(prefix)
                self.assertIsNotNone(identifier)
                url = bioregistry.resolve_identifier.get_identifiers_org_iri(prefix, identifier)
                # TODO better consider entries with bananas that aren't in identifiers.org,
                # such as chembl and xmetdb (both very different kinds of cases)
                if url is not None:
                    self.assertIsInstance(url, str)
                    res = self.session.get(url, allow_redirects=False)
                    self.assertEqual(302, res.status_code, msg=f"failed with URL: {url}")

    @unittest.skip
    def test_url_auto(self):
        """Test generating and resolving Identifiers.org URIs.

        .. warning::

            This test takes up to 5 minutes since it makes a lot of web requests, and
            is therefore skipped by default.
        """
        for prefix, entry in bioregistry.read_registry().items():
            miriam_prefix = entry.get_identifiers_org_prefix()
            if miriam_prefix is None or prefix in IDOT_BROKEN:
                continue

            identifier = entry.get_example()
            with self.subTest(prefix=prefix, identifier=identifier):
                self.assertIsNotNone(identifier, msg="All MIRIAM entries should have an example")

                url = get_identifiers_org_iri(prefix, identifier)
                self.assertIsNotNone(url, msg="All MIRIAM entries should be formattable")
                # this test is skipped because there's additional logic for constructing MIRIAM CURIEs
                # self.assertTrue(
                #     url.startswith(f"https://identifiers.org/{miriam_prefix}:"),
                #     msg=f"bad prefix for {prefix}. Expected {miriam_prefix} in {url}",
                # )
                res = self.session.get(url, allow_redirects=False)
                self.assertEqual(
                    302,
                    res.status_code,
                    msg="\n"
                    + dedent(
                        f"""\
                Prefix:     {prefix}
                Identifier: {identifier}
                URL:        {url}
                Text: """
                    )
                    + fill(res.text, 70, subsequent_indent="      "),
                )

    def test_url(self):
        """Test formatting URLs."""
        for prefix, identifier, expected, _reason in [
            ("efo", "0000400", "efo:0000400", "test simple concatenation"),
            ("chebi", "CHEBI:1234", "CHEBI:1234", "test redundant namespace (standard)"),
            ("chebi", "1234", "CHEBI:1234", "test exclusion of redundant namespace (standard)"),
            (
                "mzspec",
                "PXD002255::ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2",
                "mzspec:PXD002255::ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2",
                "test simple concatenation with false banana",
            ),
            (
                "mzspec",
                "mzspec:PXD002255::ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2",
                "mzspec:PXD002255::ES_XP_Ubi_97H_HCD_349:scan:9617:LAEIYVNSSFYK/2",
                "test simple concatenation (redundant) with false banana",
            ),
        ]:
            with self.subTest(p=prefix, i=identifier):
                curie = get_identifiers_org_curie(prefix, identifier)
                self.assertEqual(expected, curie, msg="wrong CURIE")

                url = get_identifiers_org_iri(prefix, identifier)
                self.assertEqual(f"https://identifiers.org/{curie}", url, msg="wrong URL")

                # Check that the URL resolves
                res = self.session.get(url, allow_redirects=False)
                self.assertEqual(302, res.status_code, msg=res.reason)
