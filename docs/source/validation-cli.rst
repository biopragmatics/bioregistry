Validation CLI
==============

The Bioregistry packages a set of CLI tools in the subcommand ``bioregistry validate``
that can be used to check the prefix map in a JSON-LD, Turtle, and eventually other
document formats for their conformance to the Bioregistry and offer actionable
suggestions for improvement.

Validating JSON-LD
------------------

The ``bioregistry validate jsonld`` that can be used to check the prefix map in a
JSON-LD document (either a local file or remote) conform to the Bioregistry.

For example, running the following returns a system exit of 1 because Bioregistry
collections indeed are Bioregistry-compliant by construction:

.. code-block:: console

    $ bioregistry validate jsonld "https://bioregistry.io/api/collection/0000002?format=context"

However, the Prefix Commons vendored Gene Ontology (GO) context is not valid against the
Bioregistry. It can be checked with:

.. code-block:: console

    $ bioregistry validate jsonld "https://raw.githubusercontent.com/prefixcommons/prefixcommons-py/master/prefixcommons/registry/go_context.jsonld" --tablefmt rst

============== ===================================================================== ========================= =======================================
prefix         uri_prefix                                                            issue                     solution
============== ===================================================================== ========================= =======================================
BIOMD          `http://www.ebi.ac.uk/compneur-srv/biomodels-main/publ-model.do?mid=` non-standard CURIE prefix Switch to standard prefix: biomodels.db
COG_Function   `http://www.ncbi.nlm.nih.gov/COG/grace/shokog.cgi?fun=`               unknown CURIE prefix
WB             `http://identifiers.org/wormbase/`                                    non-standard CURIE prefix Switch to standard prefix: wormbase
FBbt           `http://purl.obolibrary.org/obo/FBbt_`                                non-standard CURIE prefix Switch to standard prefix: fbbt
KEGG_LIGAND    `http://www.genome.jp/dbget-bin/www_bget?cpd:`                        non-standard CURIE prefix Switch to standard prefix: kegg.ligand
PSO_GIT        `https://github.com/Planteome/plant-stress-ontology/issues/`          unknown CURIE prefix
MaizeGDB_stock `http://maizegdb.org/data_center/stock?id=`                           unknown CURIE prefix
...
============== ===================================================================== ========================= =======================================

There are two things that might be the problem. First, the resource might use stylized
(i.e. mixed case) prefixes. Therefore, we could try passing ``--use-preferred`` to
respect prefix stylization

.. code-block:: console

    $ bioregistry validate jsonld --use-preferred "https://raw.githubusercontent.com/prefixcommons/prefixcommons-py/master/prefixcommons/registry/go_context.jsonld"

============== ===================================================================== ========================= ========================================
prefix         uri_prefix                                                            issue                     solution
============== ===================================================================== ========================= ========================================
BIOMD          `http://www.ebi.ac.uk/compneur-srv/biomodels-main/publ-model.do?mid=` non-standard CURIE prefix Switch to preferred prefix: biomodels.db
COG_Function   `http://www.ncbi.nlm.nih.gov/COG/grace/shokog.cgi?fun=`               unknown CURIE prefix
WB             `http://identifiers.org/wormbase/`                                    non-standard CURIE prefix Switch to preferred prefix: WormBase
KEGG_LIGAND    `http://www.genome.jp/dbget-bin/www_bget?cpd:`                        non-standard CURIE prefix Switch to preferred prefix: kegg.ligand
PSO_GIT        `https://github.com/Planteome/plant-stress-ontology/issues/`          unknown CURIE prefix
MaizeGDB_stock `http://maizegdb.org/data_center/stock?id=`                           unknown CURIE prefix
NCBI_GP        `http://www.ncbi.nlm.nih.gov/entrez/viewer.fcgi?db=protein&val=`      unknown CURIE prefix
...
============== ===================================================================== ========================= ========================================

Second, we could use a pre-defined community context that might have deviations from the
vanilla Bioregistry context using the ``--context`` option in combination with one of
the contexts' keys (see `all contexts <https://bioregistry.io/context/>`_):

.. code-block:: console

    $ bioregistry validate jsonld --context obo "https://raw.githubusercontent.com/prefixcommons/prefixcommons-py/master/prefixcommons/registry/go_context.jsonld"

============== ===================================================================== ========================= =======================================
prefix         uri_prefix                                                            issue                     solution
============== ===================================================================== ========================= =======================================
BIOMD          `http://www.ebi.ac.uk/compneur-srv/biomodels-main/publ-model.do?mid=` non-standard CURIE prefix Switch to standard prefix: biomodels.db
COG_Function   `http://www.ncbi.nlm.nih.gov/COG/grace/shokog.cgi?fun=`               unknown CURIE prefix
WB             `http://identifiers.org/wormbase/`                                    non-standard CURIE prefix Switch to standard prefix: WormBase
KEGG_LIGAND    `http://www.genome.jp/dbget-bin/www_bget?cpd:`                        unknown CURIE prefix
PSO_GIT        `https://github.com/Planteome/plant-stress-ontology/issues/`          unknown CURIE prefix
MaizeGDB_stock `http://maizegdb.org/data_center/stock?id=`                           unknown CURIE prefix
NCBI_GP        `http://www.ncbi.nlm.nih.gov/entrez/viewer.fcgi?db=protein&val=`      unknown CURIE prefix
...
============== ===================================================================== ========================= =======================================

It turns out that the GO JSON-LD file doesn't even validate against the OBO context!

Validating RDF in Turtle
------------------------

RDF data stored in Turtle files typically begins with a stanza defining a prefix map.
For example, one of the turtle files in the `Chemotion Knowledge Graph (Chemotion-KG)
<https://github.com/ISE-FIZKarlsruhe/chemotion-kg/tree/4cb5c24af6494d66fb8cd849921131dbc789c163>`_
begins with the following six prefixes:

.. code-block:: turtle

    @prefix nfdicore: <https://nfdi.fiz-karlsruhe.de/ontology/> .
    @prefix ns1: <http://purls.helmholtz-metadaten.de/mwo/> .
    @prefix ns2: <http://purl.obolibrary.org/obo/chebi/> .
    @prefix obo: <http://purl.obolibrary.org/obo/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

The ``bioregistry validate jsonld`` command can be used to check the prefix map in this
file and give feedback on non-standard CURIE prefix usage, unknown CURIE prefixes, etc.
while giving suggestions for fixes, when possible.

Running the command on the file that contains the example prefixes from above gives the
following output:

.. code-block::

    $ bioregistry validate ttl --tablefmt rst https://github.com/ISE-FIZKarlsruhe/chemotion-kg/raw/4cb5c24af/processing/output_bfo_compliant.ttl

======== ======================================== ========================= ==================================================================
prefix   uri_prefix                               issue                     solution
======== ======================================== ========================= ==================================================================
nfdicore https://nfdi.fiz-karlsruhe.de/ontology/  non-standard CURIE prefix Switch to standard prefix: nfdi.core
ns1      http://purls.helmholtz-metadaten.de/mwo/ unknown CURIE prefix      Consider switching to the more specific CURIE/URI prefix pair mwo:
                                                                            `http://purls.helmholtz-metadaten.de/mwo/mwo_`
ns2      http://purl.obolibrary.org/obo/chebi/    unknown CURIE prefix
======== ======================================== ========================= ==================================================================


Validating Prefix Maps in LinkML
--------------------------------

`LinkML <https://linkml.io>`_ enables defining a data model with YAML. Each definition
also includes a prefix map, which can be validate against the Bioregistry. Here's an
abridged excerpt of one `such configuration
<https://github.com/HendrikBorgelt/CatCore/blob/main/src/catcore/schema/catcore.yaml>`_:

.. code-block:: yaml

    id: https://w3id.org/nfdi4cat/catcore
    name: catcore-metadata
    title: CatCore Metadata Reference Model

    prefixes:
      catcore: https://w3id.org/nfdi4cat/catcore/
      voc4cat: https://w3id.org/nfdi4cat/voc4cat_
      CHMO: http://purl.obolibrary.org/obo/CHMO_
      OBI: http://purl.obolibrary.org/obo/OBI_
      AFR: http://purl.allotrope.org/ontologies/result#AFR_
      AFP: http://purl.allotrope.org/ontologies/process#AFP_
      AFQ: http://purl.allotrope.org/ontologies/quality#AFQ_
      NCIT: http://purl.obolibrary.org/obo/NCIT_
      nmrCV: 'http://nmrML.org/nmrCV#NMR:'
      linkml: https://w3id.org/linkml/
      AFRL: http://purl.allotrope.org/ontologies/role#AFRL_
      APOLLO_SV: http://purl.obolibrary.org/obo/APOLLO_SV_
      SIO: http://semanticscience.org/resource/SIO_

    default_prefix: catcore

The ``bioregistry validate linkml`` command can be used to check the prefix map in this
file and give feedback on non-standard CURIE prefix usage, unknown CURIE prefixes, etc.
while giving suggestions for fixes, when possible.

Running the command on the file that contains the example prefixes from above gives the
following output:

.. code-block::

    $ bioregistry validate linkml --tablefmt rst --use-preferred https://github.com/HendrikBorgelt/CatCore/raw/refs/heads/main/src/catcore/schema/catcore.yaml

======= =================================================== ========================= ===============================
prefix  uri_prefix                                          issue                     solution
======= =================================================== ========================= ===============================
catcore `https://w3id.org/nfdi4cat/catcore/`                unknown CURIE prefix
AFR     `http://purl.allotrope.org/ontologies/result#AFR_`  unknown CURIE prefix
AFP     `http://purl.allotrope.org/ontologies/process#AFP_` unknown CURIE prefix
AFQ     `http://purl.allotrope.org/ontologies/quality#AFQ_` unknown CURIE prefix
nmrCV   `http://nmrML.org/nmrCV#NMR:`                       non-standard CURIE prefix Switch to preferred prefix: NMR
AFRL    `http://purl.allotrope.org/ontologies/role#AFRL_`   unknown CURIE prefix
SIO     `http://semanticscience.org/resource/SIO_`          non-standard CURIE prefix Switch to preferred prefix: sio
======= =================================================== ========================= ===============================

Note that LinkML is developed by members of the OBO Community, and therefore, its
prefixes often skew towards OBO community preferences. Therefore, you might want to use
the ``--use-preferred`` flag.
