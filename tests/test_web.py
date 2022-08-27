# -*- coding: utf-8 -*-

"""Test for web."""

import unittest
from typing import List

from bioregistry.app.impl import get_app


class TestWeb(unittest.TestCase):
    """Tests for the web application."""

    def setUp(self) -> None:
        """Set up the test case with an app."""
        self.app = get_app()

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
                    self.assertEqual(200, res.status_code)

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
            ["json", "yaml", "turtle", "jsonld", "context"],
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
