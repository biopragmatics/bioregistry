"""Tests for the local SPARQL endpoint."""

import unittest
from typing import ClassVar

from curies.mapping_service.utils import (
    CONTENT_TYPE_SYNONYMS,
    sparql_service_available,
    get_sparql_records,
    get_sparql_record_so_tuples,
)
from curies.mapping_service import MappingServiceGraph, MappingServiceSPARQLProcessor
from bioregistry import Manager

PING_SPARQL = 'SELECT ?s ?o WHERE { BIND("hello" as ?s) . BIND("there" as ?o) . }'
LOCAL_BIOREGISTRY = "http://localhost:5000/sparql"
LOCAL_BLAZEGRAPH = "http://192.168.2.30:9999/blazegraph/sparql"

SPARQL = f"""\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?s ?o WHERE {{
    SERVICE <{LOCAL_BIOREGISTRY}> {{
        VALUES ?s {{ <http://purl.obolibrary.org/obo/CHEBI_24867> }}
        ?s owl:sameAs ?o
    }}
}}
""".rstrip()


class TestMappingGraph(unittest.TestCase):
    """A test case for the mapping service graph."""

    manager: ClassVar[Manager]
    graph: ClassVar[MappingServiceGraph]

    @classmethod
    def setUpClass(cls) -> None:
        """Add a manager and service graph to the test case."""
        cls.manager = Manager()
        cls.graph = MappingServiceGraph(converter=cls.manager.converter)
        cls.processor = MappingServiceSPARQLProcessor(graph=cls.graph)

    def test_ensembl(self):
        """Test mapping over ensembl.

        Suggested by Olaf in https://github.com/biopragmatics/bioregistry/issues/803
        """
        sparql = """\
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?o WHERE {
            <http://identifiers.org/ensembl/ENSG00000006125> owl:sameAs ?o
        }
        """
        results = self.graph.query(sparql, processor=self.processor)


@unittest.skipUnless(
    sparql_service_available(LOCAL_BIOREGISTRY), reason="No local Bioregistry is running"
)
class TestSPARQL(unittest.TestCase):
    """Tests for SPARQL."""

    @unittest.skipUnless(
        sparql_service_available(LOCAL_BLAZEGRAPH), reason="No local BlazeGraph is running"
    )
    def test_federate_blazegraph(self):
        """Test federating on a blazegraph.

        How to run blazegraph locally:

        1. Get: https://github.com/blazegraph/database/releases/download/BLAZEGRAPH_2_1_6_RC/blazegraph.jar
        2. Run: java -jar blazegraph.jar
        """
        mimetypes = set(CONTENT_TYPE_SYNONYMS).union(CONTENT_TYPE_SYNONYMS.values())
        for mimetype, query in sorted(mimetypes):
            with self.subTest(mimetype=mimetype):
                records = get_sparql_records(LOCAL_BLAZEGRAPH, SPARQL, accept=mimetype)
                self.assertIn(
                    ("http://purl.obolibrary.org/obo/CHEBI_24867", "https://bioregistry.io/chebi:24867"),
                    get_sparql_record_so_tuples(records),
                )
