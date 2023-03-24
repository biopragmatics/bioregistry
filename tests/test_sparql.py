"""Tests for the local SPARQL endpoint."""

import unittest

import requests

PING_SPARQL = 'SELECT ?test WHERE { BIND("hello" as ?test) }'
LOCAL_BIOREGISTRY = "http://localhost:5000/sparql"
LOCAL_BLAZEGRAPH = "http://192.168.2.30:9999/blazegraph/sparql"


def get(endpoint: str, sparql: str, accept):
    """Get a response from a given SPARQL query."""
    response = requests.get(
        endpoint,
        params={"query": sparql},
        headers={"accept": accept},
    )
    res_json = response.json()
    return [
        {key: values["value"] for key, values in record.items()}
        for record in res_json["results"]["bindings"]
    ]


def sparql_service_available(endpoint: str) -> bool:
    """Test if a SPARQL service is running."""
    try:
        records = get(endpoint, PING_SPARQL, "application/json")
    except requests.exceptions.ConnectionError:
        return False
    return 1 == len(records) and "hello" == records[0]["test"]


SPARQL = f"""\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?o WHERE {{
    SERVICE <{LOCAL_BIOREGISTRY}> {{
        <http://purl.obolibrary.org/obo/CHEBI_24867> owl:sameAs ?o
    }}
}}
""".rstrip()


@unittest.skipUnless(
    sparql_service_available(LOCAL_BIOREGISTRY), reason="No local Bioregistry is running"
)
class TestSPARQL(unittest.TestCase):
    """Tests for SPARQL."""

    def assert_endpoint(self, endpoint: str):
        """Assert the endpoint returns favorable results."""
        records = get(endpoint, SPARQL, accept="application/json")
        self.assertIn("https://bioregistry.io/chebi:24867", {record["o"] for record in records})

    @unittest.skipUnless(
        sparql_service_available(LOCAL_BLAZEGRAPH), reason="No local BlazeGraph is running"
    )
    def test_federate_blazegraph(self):
        """Test federating on a blazegraph.

        How to run blazegraph locally:

        1. Get: https://github.com/blazegraph/database/releases/download/BLAZEGRAPH_2_1_6_RC/blazegraph.jar
        2. Run: java -jar blazegraph.jar
        """
        self.assert_endpoint(LOCAL_BLAZEGRAPH)
