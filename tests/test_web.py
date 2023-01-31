# -*- coding: utf-8 -*-

"""Test for web."""

import json
import unittest
from typing import List

import rdflib
import yaml

from bioregistry import Collection, Manager
from bioregistry.app.impl import get_app


class TestWeb(unittest.TestCase):
    """Tests for the web application."""

    def setUp(self) -> None:
        """Set up the test case with an app."""
        self.app = get_app()
        self.manager = Manager()

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
                # API
                "apidocs",
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

    def test_api_invalid_format(self):
        """Test when an invalid `format` parameter is given.

        .. seealso:: https://github.com/biopragmatics/bioregistry/issues/715
        """
        with self.app.test_client() as client:
            res = client.get("/api/registry/3dmet?format=nope")
            self.assertEqual(400, res.status_code)

    def test_api_registry(self):
        """Test the registry endpoint."""
        self.assert_endpoint(
            "/api/registry",
            ["yaml", "json"],
        )

    def test_api_resource(self):
        """Test the resource endpoint."""
        self.assert_endpoint(
            "/api/registry/3dmet",
            ["yaml", "json"],
        )

        # test something that's wrong gives a proper error
        with self.app.test_client() as client:
            with self.subTest(fmt=None):
                res = client.get("/api/registry/nope")
                self.assertEqual(404, res.status_code)

    def test_ui_resource_rdf(self):
        """Test the UI resource with content negotiation."""
        prefix = "3dmet"
        for accept, format in [
            ("text/turtle", "turtle"),
            ("text/n3", "n3"),
            ("application/ld+json", "jsonld"),
        ]:
            with self.subTest(format=format), self.app.test_client() as client:
                res = client.get(f"/registry/{prefix}", headers={"Accept": accept})
                self.assertEqual(
                    200, res.status_code, msg=f"Failed on {prefix} to accept {accept} ({format})"
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
                    g.query("SELECT ?s WHERE { ?s a <https://bioregistry.io/schema/#0000001> }")
                )
                self.assertEqual(1, len(results))
                self.assertEqual(f"https://bioregistry.io/registry/{prefix}", str(results[0][0]))

    def test_api_metaregistry(self):
        """Test the metaregistry endpoint."""
        self.assert_endpoint(
            "/api/metaregistry",
            ["json", "yaml"],
        )

    def test_api_metaresource(self):
        """Test the metaresource endpoint."""
        self.assert_endpoint(
            "/api/metaregistry/miriam",
            ["json", "yaml", "turtle", "jsonld"],
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

    def test_api_reference(self):
        """Test the reference endpoint."""
        self.assert_endpoint(
            "/api/reference/chebi:24867",
            ["json", "yaml"],
        )

    def test_api_collections(self):
        """Test the collections endpoint."""
        self.assert_endpoint(
            "/api/collections",
            ["json", "yaml"],
        )

    def test_api_collection(self):
        """Test the collection endpoint."""
        self.assert_endpoint(
            "/api/collection/0000001",
            ["json", "yaml", "turtle", "jsonld"],
        )

        with self.app.test_client() as client:
            res = client.get("api/collection/0000001.context.jsonld").json
            self.assertIn("@context", res)
            self.assertIn("biostudies", res["@context"])

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

    def test_api_contexts(self):
        """Test the contexts endpoint."""
        self.assert_endpoint(
            "/api/contexts",
            ["json", "yaml"],
        )

    def test_api_context(self):
        """Test the context endpoint."""
        self.assert_endpoint(
            "/api/context/obo",
            ["json", "yaml"],
        )

    def test_api_contributors(self):
        """Test the contributors endpoint."""
        self.assert_endpoint(
            "/api/contributors",
            ["json", "yaml"],
        )

    def test_api_contributor(self):
        """Test the contributor endpoint."""
        self.assert_endpoint(
            "/api/contributor/0000-0003-4423-4370",
            ["json", "yaml"],
        )

    def assert_endpoint(self, endpoint: str, formats: List[str]) -> None:
        """Test downloading the full registry as JSON."""
        self.assertTrue(endpoint.startswith("/"))
        with self.app.test_client() as client:
            with self.subTest(fmt=None):
                res = client.get(endpoint)
                self.assertEqual(200, res.status_code)
            for fmt in formats:
                url = f"{endpoint}?format={fmt}"
                with self.subTest(fmt=fmt, endpoint=url):
                    res = client.get(url)
                    self.assertEqual(200, res.status_code)

    def test_missing_prefix(self):
        """Test missing prefix responses."""
        with self.app.test_client() as client:
            for query in ["xxxx", "xxxx:yyyy"]:
                with self.subTest(query=query):
                    res = client.get(f"/{query}")
                    self.assertEqual(404, res.status_code)

    def test_search(self):
        """Test search."""
        with self.app.test_client() as client:
            res = client.get("/api/search?q=che")
            self.assertEqual(200, res.status_code)

    def test_autocomplete(self):
        """Test search."""
        with self.app.test_client() as client:
            for q in ["che", "chebi", "xxxxx", "chebi:123", "chebi:dd"]:
                with self.subTest(query=q):
                    res = client.get(f"/api/autocomplete?q={q}")
                    self.assertEqual(200, res.status_code)

    def test_resolve_failures(self):
        """Test resolve failures."""
        with self.app.test_client() as client:
            for endpoint in ["chebi:ddd", "xxx:yyy", "gmelin:1"]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint)
                    self.assertEqual(404, res.status_code)

    def test_redirects(self):
        """Test healthy redirects."""
        with self.app.test_client() as client:
            for endpoint in [
                "metaregistry/miriam/chebi:24867",
                "chebi:24867",
                "health/go",
            ]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint)
                    self.assertEqual(302, res.status_code)

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
