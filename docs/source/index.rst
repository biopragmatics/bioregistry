Bioregistry |release| Documentation
===================================
The Bioregistry is an integrative, open, community-driven meta-registry
of databases, ontologies, and other nomenclature resources in the life sciences.
It relies on an open code, open data, and open infrastructure paradigm to support
its longevity along with a sustainable governance model that enables community
curation and discussion.

This documentation is specifically for the Python package that can
access the Bioregistry and use it for common tasks like metadata lookup,
CURIE expansion, URI contraction, and more.

.. seealso::

    - `About this project <https://bioregistry.io/summary>`_
    - `Bioregistry Website <https://bioregistry.io>`_
    - `A list of all prefixes <https://bioregistry.io/registry/>`_
    - `Source Code on GitHub <https://github.com/biopragmatics/bioregistry>`_
    - `Data Downloads <https://github.com/biopragmatics/bioregistry/tree/main/exports>`_
    - `Project Governance <https://github.com/biopragmatics/bioregistry/blob/main/docs/GOVERNANCE.md>`_
    - `Contribution Guidelines <https://github.com/biopragmatics/bioregistry/blob/main/docs/CONTRIBUTING.md>`_
    - `Programming language-agnostic API <https://bioregistry.io/apidocs>`_
    - `Python Package on PyPI <https://pypi.org/project/bioregistry>`_
    - `Docker container on DockerHub <https://hub.docker.com/r/biopragmatics/bioregistry>`_

Installation
------------
The most recent release of the Bioregistry Python package can be installed from
`PyPI <https://pypi.org/project/bioregistry>`_ with:

.. code-block:: shell

    $ pip install bioregistry

The most recent code and data can be installed directly from GitHub with:

.. code-block:: shell

    $ pip install git+https://github.com/biopragmatics/bioregistry.git

To install in development mode, use the following:

.. code-block:: shell

    $ git clone git+https://github.com/biopragmatics/bioregistry.git
    $ cd bioregistry
    $ pip install -e .


.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :name: start

   reference
   alignment
   cli
   pandas
   deployment

Indices and Tables
------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
