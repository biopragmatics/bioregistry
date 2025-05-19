Validation CLI
==============

The Bioregistry packages a CLI tool ``bioregistry validate jsonld`` that can be used to
check the prefix map in a JSON-LD document (either a local file or remote) conform to
the Bioregistry.

For example, running the following returns a system exit of 1 because Bioregistry
collections indeed are Bioregistry-compliant by construction:

.. code-block:: console

    $ bioregistry validate jsonld "https://bioregistry.io/api/collection/0000002?format=context"

However, the Prefix Commons vendored Gene Ontology (GO) context is not valid against the
Bioregistry. It can be checked with:

.. code-block:: console

    $ bioregistry validate jsonld "https://raw.githubusercontent.com/prefixcommons/prefixcommons-py/master/prefixcommons/registry/go_context.jsonld"
    BIOMD - nonstandard > Switch to standard prefix: biomodels.db
    COG_Function - invalid
    WB - nonstandard > Switch to standard prefix: wormbase
    FBbt - nonstandard > Switch to standard prefix: fbbt
    KEGG_LIGAND - nonstandard > Switch to standard prefix: kegg.ligand
    PSO_GIT - invalid
    MaizeGDB_stock - invalid
    ...

There are two things that might be the problem. First, the resource might use stylized
(i.e. mixed case) prefixes. Therefore, we could try passing ``--use-preferred`` to
respect prefix stylization

.. code-block:: console

    $ bioregistry validate jsonld --use-preferred "https://raw.githubusercontent.com/prefixcommons/prefixcommons-py/master/prefixcommons/registry/go_context.jsonld"
    BIOMD - nonstandard > Switch to preferred prefix: biomodels.db
    COG_Function - invalid
    WB - nonstandard > Switch to preferred prefix: WormBase
    KEGG_LIGAND - nonstandard > Switch to preferred prefix: kegg.ligand
    PSO_GIT - invalid
    MaizeGDB_stock - invalid
    ...

Second, we could use a pre-defined community context that might have deviations from the
vanilla Bioregistry context using the ``--context`` option in combination with one of
the contexts' keys (see all contexts here: https://bioregistry.io/context/):

.. code-block:: console

    $ bioregistry validate jsonld --context obo "https://raw.githubusercontent.com/prefixcommons/prefixcommons-py/master/prefixcommons/registry/go_context.jsonld"
    BIOMD - nonstandard > Switch to preferred prefix: biomodels.db
    COG_Function - invalid
    WB - nonstandard > Switch to preferred prefix: WormBase
    KEGG_LIGAND - invalid
    PSO_GIT - invalid
    MaizeGDB_stock - invalid
    ...

It turns out that the GO JSON-LD file doesn't even validate against the OBO context!
