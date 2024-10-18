# -*- coding: utf-8 -*-

"""Test for web."""

import json
import unittest
from typing import ClassVar, Dict, List

import rdflib
import rdflib.plugins.parsers.notation3
import yaml
from fastapi import FastAPI
from starlette.testclient import TestClient

from bioregistry import Resource
from bioregistry.app.api import MappingResponse, URIResponse
from bioregistry.app.impl import get_app
from bioregistry.utils import pydantic_parse


class TestWeb(unittest.TestCase):
    """Tests for the web application."""

    fastapi: ClassVar[FastAPI]
    client: ClassVar[TestClient]

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test case with an app."""
        cls.fastapi = get_app()
        cls.client = TestClient(cls.fastapi)

    def test_api_registry(self):
        """Test the registry endpoint."""
        fail_endpoint = "/api/registry?format=FAIL"
        with self.subTest(endpoint=fail_endpoint):
            res = self.client.get(fail_endpoint)
            self.assertEqual(400, res.status_code)

        for endpoint, parse_func in [
            ("/api/registry", self._parse_registry_json),
            ("/api/registry?format=json", self._parse_registry_json),
            ("/api/registry?format=yaml", self._parse_registry_yaml),
            # ("/api/registry?format=turtle", partial(self._parse_registry_rdf, format="turtle")),
        ]:
            with self.subTest(endpoint=endpoint):
                self._test_registry(endpoint, parse_func)

    def _test_registry(self, endpoint, parse_func):
        res = self.client.get(endpoint)
        self.assertEqual(200, res.status_code)
        self.assertIsInstance(res.text, str)
        registry = parse_func(res)
        self.assertIn("chebi", registry)
        self.assertEqual("CHEBI", registry["chebi"].get_preferred_prefix())

    @staticmethod
    def _parse_registry_json(res) -> Dict[str, Resource]:
        data = res.json().items()
        return {key: pydantic_parse(Resource, resource) for key, resource in data}

    def _parse_registry_rdf(self, res, fmt: str) -> Dict[str, Resource]:
        graph = rdflib.Graph()
        try:
            graph.parse(data=res.text, format=fmt)
        except rdflib.plugins.parsers.notation3.BadSyntax:
            self.fail(f"Bad syntax for format {fmt}:\n\n{res.text}")
        sparql = """\
        SELECT ?prefix ?description ?homepage ?uri_format ?example
        WHERE {
            ?resource a bioregistry.schema:0000001 ;
                dcterms:description ?description ;
                foaf:homepage ?homepage ;
                bioregistry.schema:0000029 ?prefix ;
                bioregistry.schema:0000006 ?uri_format ;
                bioregistry.schema:0000005 ?example ;
        }
        """
        rv = {}
        for record in graph.query(sparql):
            prefix = record["prefix"]["value"]
            rv[prefix] = Resource(
                prefix=prefix,
                description=record["description"]["value"],
                homepage=record["homepage"]["value"],
                uri_format=record["uri_format"]["value"],
                example=record["example"]["value"],
            )
        return rv

    @staticmethod
    def _parse_registry_yaml(res) -> Dict[str, Resource]:
        data = yaml.safe_load(res.text).items()
        return {key: pydantic_parse(Resource, resource) for key, resource in data}

    def test_api_resource(self):
        """Test the resource endpoint."""
        res = self.client.get("/api/registry/3dmet?format=nope")
        self.assertEqual(400, res.status_code)

        self.assert_endpoint(
            "/api/registry/3dmet",
            ["yaml", "json"],
        )

        # test something that's wrong gives a proper error
        with self.subTest(fmt=None):
            res = self.client.get("/api/registry/nope")
            self.assertEqual(404, res.status_code)

    def test_ui_resource_rdf(self):
        """Test the UI resource with content negotiation."""
        prefix = "3dmet"
        for accept, fmt in [
            ("text/turtle", "turtle"),
            ("text/n3", "n3"),
            ("application/ld+json", "jsonld"),
        ]:
            with self.subTest(format=fmt):
                res = self.client.get(f"/registry/{prefix}", headers={"Accept": accept})
                self.assertEqual(
                    200, res.status_code, msg=f"Failed on {prefix} to accept {accept} ({fmt})"
                )
                self.assertEqual(accept, res.request.headers.get("Accept", []))
                if fmt == "jsonld":
                    continue
                with self.assertRaises(ValueError, msg="result was return as JSON"):
                    json.loads(res.text)
                g = rdflib.Graph()
                g.parse(data=res.text, format=fmt)

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

    def test_api_reference(self):
        """Test the reference endpoint."""
        for value in [
            "/api/reference/chebi:24867",
            "/api/reference/ctri:CTRI/2023/04/052053",  # check paths are accepted
        ]:
            self.assert_endpoint(
                value,
                ["json", "yaml"],
            )

    def test_api_collections(self):
        """Test the collections endpoint."""
        self.assert_endpoint(
            "/api/collection",
            ["json", "yaml"],
        )

    def test_api_collection(self):
        """Test the collection endpoint."""
        self.assert_endpoint(
            "/api/collection/0000001",
            ["json", "yaml", "turtle", "jsonld"],
        )

        res = self.client.get("/api/collection/0000001?format=context").json()
        self.assertIn("@context", res)
        self.assertIn("biostudies", res["@context"])

    def test_api_contexts(self):
        """Test the contexts endpoint."""
        self.assert_endpoint(
            "/api/context",
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
        with self.subTest(fmt=None):
            res = self.client.get(endpoint)
            self.assertEqual(200, res.status_code)
        for fmt in formats:
            url = f"{endpoint}?format={fmt}"
            with self.subTest(fmt=fmt, endpoint=url):
                res = self.client.get(url)
                self.assertEqual(200, res.status_code, msg=f"\n\n{res.text}")

    def test_search(self):
        """Test search."""
        res = self.client.get("/api/search?q=che")
        self.assertEqual(200, res.status_code, msg=f"\n\n{res.text}")

    def test_autocomplete(self):
        """Test search."""
        for q in ["che", "chebi", "xxxxx", "chebi:123", "chebi:dd"]:
            with self.subTest(query=q):
                res = self.client.get(f"/api/autocomplete?q={q}")
                self.assertEqual(200, res.status_code)

    def test_external_registry_mappings(self):
        """Test external registry mappings."""
        url = "/api/metaregistry/obofoundry/mapping/bioportal"
        res = self.client.get(url)
        res_parsed = pydantic_parse(MappingResponse, res.json())
        self.assertEqual("obofoundry", res_parsed.meta.source)
        self.assertEqual("bioportal", res_parsed.meta.target)
        self.assertIn("gaz", res_parsed.mappings)
        self.assertEqual("GAZ", res_parsed.mappings["gaz"])
        # This is an obsolete OBO Foundry ontology so it won't get uploaded to BioPortal
        self.assertIn("loggerhead", res_parsed.meta.source_only)
        # This is a non-ontology so it won't get in OBO Foundry
        self.assertIn("DCTERMS", res_parsed.meta.target_only)

    def test_iri_mapping(self):
        """Test IRI mappings.

        .. seealso:: https://github.com/biopragmatics/bioregistry/issues/1065
        """
        uri = "http://id.nlm.nih.gov/mesh/C063233"
        res = self.client.post("/api/uri/parse/", json={"uri": uri})
        self.assertEqual(200, res.status_code)
        data = pydantic_parse(URIResponse, res.json())
        self.assertEqual(uri, data.uri)
        self.assertIn("https://meshb.nlm.nih.gov/record/ui?ui=C063233", data.providers.values())

        # Bad URI
        uri = "xxxx"
        res = self.client.post("/api/uri/parse/", json={"uri": uri})
        self.assertEqual(404, res.status_code)
