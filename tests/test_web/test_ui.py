"""Test for web."""

from __future__ import annotations

import json
import unittest

import rdflib
import yaml

from bioregistry import Collection
from bioregistry.app.impl import get_app


class TestUI(unittest.TestCase):
    """Tests for the UI."""

    def setUp(self) -> None:
        """Set up the test case with an app."""
        _, self.app = get_app(return_flask=True)
        self.manager = self.app.manager

    def test_ui(self):
        """Test user-facing pages don't error."""
        with self.app.test_client() as client:
            for endpoint in [
                "",
                "registry",
                "registry/chebi",
                "metaregistry",
                "metaregistry/miriam",
                "metaregistry/miriam/chebi",
                # "metaregistry/miriam/chebi:24867",  # FIXME this resolves, test elsewhere
                "reference/chebi:24867",
                "collection",
                "collection/0000001",
                "context",
                "context/obo",
                "contributors",
                "contributor/0000-0003-4423-4370",
                # Meta pages
                "download",
                "summary",
                "usage",
                "schema",
                "sustainability",
                "related",
                "acknowledgements",
            ]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint, follow_redirects=True)
                    self.assertEqual(
                        200, res.status_code, msg=f"Endpoint: {endpoint}\n\n{res.text}"
                    )
                    with self.assertRaises(
                        ValueError, msg=f"Content should not be JSON-parsable. Endpoint: {endpoint}"
                    ):
                        json.loads(res.text)

    def test_ui_collection_json(self):
        """Test the UI registry with content negotiation for json/yaml."""
        identifier = "0000001"
        for accept, loads in [
            ("application/json", json.loads),
            ("application/yaml", yaml.safe_load),
        ]:
            with self.subTest(format=format), self.app.test_client() as client:
                res = client.get(f"/collection/{identifier}", headers={"Accept": accept})
                self.assertEqual(
                    200,
                    res.status_code,
                    msg=f"Failed on {identifier} to accept {accept} ({format})",
                )
                self.assertEqual({accept}, {t for t, _ in res.request.accept_mimetypes})
                collection = Collection(**loads(res.text))
                self.assertEqual(self.manager.collections[identifier], collection)

    def test_ui_collection_rdf(self):
        """Test the UI registry with content negotiation."""
        identifier = "0000001"
        for accept, format in [
            ("text/turtle", "turtle"),
            ("text/n3", "n3"),
            ("application/ld+json", "jsonld"),
        ]:
            with self.subTest(format=format), self.app.test_client() as client:
                res = client.get(f"/collection/{identifier}", headers={"Accept": accept})
                self.assertEqual(
                    200,
                    res.status_code,
                    msg=f"Failed on {identifier} to accept {accept} ({format})",
                )
                self.assertEqual({accept}, {t for t, _ in res.request.accept_mimetypes})
                if format == "jsonld":
                    continue
                with self.assertRaises(ValueError, msg="result was return as JSON"):
                    json.loads(res.text)
                g = rdflib.Graph()
                g.parse(data=res.text, format=format)

                # Check for single prefix
                results = list(
                    g.query("SELECT ?s WHERE { ?s a <https://bioregistry.io/schema/#0000003> }")
                )
                self.assertEqual(1, len(results))
                self.assertEqual(
                    f"https://bioregistry.io/collection/{identifier}", str(results[0][0])
                )

    def test_ui_registry_rdf(self):
        """Test the UI registry with content negotiation."""
        metaprefix = "miriam"
        for accept, format in [
            ("text/turtle", "turtle"),
            ("text/n3", "n3"),
            ("application/ld+json", "jsonld"),
        ]:
            with self.subTest(format=format), self.app.test_client() as client:
                res = client.get(f"/metaregistry/{metaprefix}", headers={"Accept": accept})
                self.assertEqual(
                    200,
                    res.status_code,
                    msg=f"Failed on {metaprefix} to accept {accept} ({format})",
                )
                self.assertEqual({accept}, {t for t, _ in res.request.accept_mimetypes})
                if format == "jsonld":
                    continue
                with self.assertRaises(ValueError, msg="result was return as JSON"):
                    json.loads(res.text)
                g = rdflib.Graph()
                g.parse(data=res.text, format=format)

                # Check for single prefix
                results = list(
                    g.query("SELECT ?s WHERE { ?s a <https://bioregistry.io/schema/#0000002> }")
                )
                self.assertEqual(1, len(results))
                self.assertEqual(
                    f"https://bioregistry.io/metaregistry/{metaprefix}", str(results[0][0])
                )

    def test_missing_prefix(self):
        """Test missing prefix responses."""
        with self.app.test_client() as client:
            for query in ["xxxx", "xxxx:yyyy"]:
                with self.subTest(query=query):
                    res = client.get(f"/{query}")
                    self.assertEqual(404, res.status_code)

    def test_resolve_failures(self):
        """Test resolve failures."""
        with self.app.test_client() as client:
            for endpoint in ["chebi:ddd", "xxx:yyy", "gmelin:1"]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint)
                    self.assertEqual(404, res.status_code)

    def test_banana_redirects(self):
        """Test banana redirects."""
        with self.app.test_client() as client:
            for prefix, identifier, location in [
                ("agrovoc", "c_2842", "http://aims.fao.org/aos/agrovoc/c_2842"),
                ("agrovoc", "2842", "http://aims.fao.org/aos/agrovoc/c_2842"),
                # Related to https://github.com/biopragmatics/bioregistry/issues/93, the app route is not greedy,
                # so it parses on the rightmost colon.
                # ("go", "0032571", "http://amigo.geneontology.org/amigo/term/GO:0032571"),
                # ("go", "GO:0032571", "http://amigo.geneontology.org/amigo/term/GO:0032571"),
            ]:
                with self.subTest(prefix=prefix, identifier=identifier):
                    res = client.get(f"/{prefix}:{identifier}", follow_redirects=False)
                    self.assertEqual(
                        302,
                        res.status_code,
                        msg=f"{prefix}\nHeaders: {res.headers}\nRequest: {res.request}",
                    )
                    self.assertEqual(location, res.headers["Location"])

    def test_redirects(self):
        """Test healthy redirects."""
        with self.app.test_client() as client:
            for endpoint in [
                "/metaregistry/miriam/chebi:24867",
                "/chebi:24867",
                "/ark:53355/cl010066723",
                "/ark:/53355/cl010066723",  # test if slash at beginning of luid works
                "/foaf:test/nope",  # test if slash in middle of luid works
                # this isn't a real FOAF term, but it's just to make sure that the resolver
                # doesn't blow up on a local unique identifier that has a colon inside it
                # i.e., foaf should still get properly recognized
                "/foaf:test:case",
                "/foaf:test:case:2",
                "/health/go",
            ]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint, follow_redirects=False)
                    self.assertEqual(302, res.status_code)  # , msg=res.text)

    def test_redirect_404(self):
        """Test 404 errors."""
        with self.app.test_client() as client:
            for endpoint in [
                "/chebi:abcd",  # wrong identifier pattern
                "/gmelin:1234",  # no providers
            ]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint, follow_redirects=False)
                    self.assertEqual(404, res.status_code)

    def test_reference_page(self):
        """Test the reference page."""
        with self.app.test_client() as client:
            for endpoint in [
                "/reference/ctri:CTRI/2023/04/052053",  # check that slashes are okay
            ]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint, follow_redirects=False)
                    self.assertEqual(200, res.status_code)
