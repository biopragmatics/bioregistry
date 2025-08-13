"""Tests for the local SPARQL endpoint."""

import unittest
from xml import etree

import requests

PING_SPARQL = 'SELECT ?s ?o WHERE { BIND("hello" as ?s) . BIND("there" as ?o) . }'
LOCAL_BIOREGISTRY = "http://localhost:5000/sparql"
LOCAL_BLAZEGRAPH = "http://192.168.2.30:9999/blazegraph/sparql"


def _handle_res_xml(res: requests.Response) -> set[tuple[str, str]]:
    root = etree.ElementTree.fromstring(res.text)
    results = root.find("{http://www.w3.org/2005/sparql-results#}results")
    rv = set()
    for result in results:
        parsed_result = {
            binding.attrib["name"]: binding.find("{http://www.w3.org/2005/sparql-results#}uri").text
            for binding in result
        }
        rv.add((parsed_result["s"], parsed_result["o"]))
    return rv


def _handle_res_json(res: requests.Response) -> set[tuple[str, str]]:
    res_json = res.json()
    return {
        (record["s"]["value"], record["o"]["value"]) for record in res_json["results"]["bindings"]
    }


def _handle_res_csv(res: requests.Response) -> set[tuple[str, str]]:
    header, *lines = (line.strip().split(",") for line in res.text.splitlines())
    records = (dict(zip(header, line)) for line in lines)
    return {(record["s"], record["o"]) for record in records}


HANDLERS = {
    "application/json": _handle_res_json,
    "application/xml": _handle_res_xml,
    "text/csv": _handle_res_csv,
}


def get(endpoint: str, sparql: str, accept) -> set[tuple[str, str]]:
    """Get a response from a given SPARQL query."""
    res = requests.get(
        endpoint,
        timeout=15,
        params={"query": sparql},
        headers={"accept": accept},
    )
    func = HANDLERS[accept]
    return func(res)


def sparql_service_available(endpoint: str) -> bool:
    """Test if a SPARQL service is running."""
    try:
        records = get(endpoint, PING_SPARQL, "application/json")
    except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
        return False
    return list(records) == [("hello", "there")]


SPARQL = f"""\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?s ?o WHERE {{
    SERVICE <{LOCAL_BIOREGISTRY}> {{
        VALUES ?s {{ <http://purl.obolibrary.org/obo/CHEBI_24867> }}
        ?s owl:sameAs ?o
    }}
}}
""".rstrip()


@unittest.skipUnless(
    sparql_service_available(LOCAL_BIOREGISTRY), reason="No local Bioregistry is running"
)
class TestSPARQL(unittest.TestCase):
    """Tests for SPARQL."""

    def assert_endpoint(self, endpoint: str, *, accept: str):
        """Assert the endpoint returns favorable results."""
        records = get(endpoint, SPARQL, accept=accept)
        self.assertIn(
            ("http://purl.obolibrary.org/obo/CHEBI_24867", "https://bioregistry.io/chebi:24867"),
            records,
        )

    @unittest.skipUnless(
        sparql_service_available(LOCAL_BLAZEGRAPH), reason="No local BlazeGraph is running"
    )
    def test_federate_blazegraph(self):
        """Test federating on a blazegraph.

        How to run blazegraph locally:

        1. Get:
           https://github.com/blazegraph/database/releases/download/BLAZEGRAPH_2_1_6_RC/blazegraph.jar
        2. Run: java -jar blazegraph.jar
        """
        for mimetype in HANDLERS:
            with self.subTest(mimetype=mimetype):
                self.assert_endpoint(LOCAL_BLAZEGRAPH, accept=mimetype)
