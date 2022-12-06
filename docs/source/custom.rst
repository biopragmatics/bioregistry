Deploying the Bioregistry
=========================
The Bioregistry web application is a part of the ``bioregistry`` Python package which is updated,
packaged, and pushed nightly to the `Python Package Index (PyPI) <https://pypi.org/project/bioregistry/>`_.
It can be installed and run interactively in the command line with the following commands:

.. code-block:: shell

    python -m pip install --upgrade gunicorn bioregistry[web]
    python -m bioregistry web \
        --port 8766 --host "0.0.0.0" \
        --with-gunicorn --workers 4 \
        --base-url http://www.host.tld \
        --registry registry.json \
        --metaregistry metaregistry.json

The Bioregistry is also containerized and pushed nightly to
`Docker Hub <https://hub.docker.com/r/biopragmatics/bioregistry>`_.
You can pull then run the latest in the command line with the following commands:

.. code-block:: shell

    docker pull biopragmatics/bioregistry:latest
    docker run --detach -i --name bioregistry -p 8766:8766 biopragmatics/bioregistry:latest

The following shell script can be used to automatically update the containerized deployment:

.. code-block:: shell

    # restart.sh
    #!/bin/bash

    # Store the container's hash
    BIOREGISTRY_CONTAINER_ID=$(docker ps --filter "name=bioregistry" -aq)

    # Stop and remove the old container, taking advantage of the fact that it's named specifically
    if [ -n "BIOREGISTRY_CONTAINER_ID" ]; then
      docker stop $BIOREGISTRY_CONTAINER_ID
      docker rm $BIOREGISTRY_CONTAINER_ID
    fi

    # Pull the latest
    docker pull biopragmatics/bioregistry:latest

    # Run the start script
    docker run --detach -i --name bioregistry -p 8766:8766 biopragmatics/bioregistry:latest

Deploying a Custom Bioregistry
==============================
This is a tutorial on how to run a custom instance of the Bioregistry.

Custom Content
--------------
In the following example, a slimmed down registry is generated from the base
Bioregistry. It's possible to add additional :class:`bioregistry.Resource`
instances from arbitrary sources.

.. code-block:: python

    import bioregistry
    from pathlib import Path

    slim_prefixes = {"chebi", "go", "ncbitaxonomy"}
    slim_registry: dict[str, bioregistry.Resource] = {
        resource.prefix: resource
        for resource in bioregistry.resources()
        if resource.prefix in slim_prefixes
    }
    bioregistry.write_registry(
        slim_registry,
        path=Path.home().joinpath("Desktop", "registry.json"),
    )

The same is possible for collections, contexts, and even the metaregistry.

Running in the command line with Python
---------------------------------------
The Bioregistry can be run from the Python shell directly following installation
from the Python Package Index. This requires the ``registry.json`` and ``metaregistry.json``
to be in the same directory, but any valid paths can be given.

.. code-block:: shell

    python -m pip install gunicorn bioregistry[web]
    python -m bioregistry web \
        --port 8766 --host "0.0.0.0" \
        --with-gunicorn --workers 4 \
        --base-url http://www.host.tld \
        --registry registry.json \
        --metaregistry metaregistry.json

Running with Docker
-------------------
Create the following ``Dockerfile`` in the same directory as the custom registry,
metaregistry, and other files.

.. code-block:: docker

    # Dockerfile
    FROM python:3.11-alpine

    COPY registry.json
    COPY metaregistry.json

    RUN python -m pip install gunicorn bioregistry[web]
    ENTRYPOINT python -m bioregistry web \
        --port 8766 --host "0.0.0.0" \
        --with-gunicorn --workers 4 \
        --base-url http://www.host.tld \
        --registry registry.json \
        --metaregistry metaregistry.json

There are two options for running the ``Dockerfile``. The first option
is by running the following two commands in the command line:

.. code-block:: shell

    # Build the docker image from the same directory as the Dockerfile
    docker build --tag bioregistry_custom:latest .

    # Run the docker image, -d means "detach"
    docker run -d -p 8766:8766 bioregistry_custom:latest

The second option is to use an additional `Docker compose <https://docs.docker.com/compose/>`_
file to orchestrate building, tagging, and running. It works by creating (yet another)
configuration file ``docker-compose.yml`` in the same directory as ``Dockerfile`` with
the following:

.. code-block:: yaml

    # docker-compose.yml
    version: '3'
    services:
      app:
        build: .
        restart: always
        ports:
          - "8766:8766"

.. note:: This is a relatively simple configuration, Docker Compose is capable of much more than this in general

The following command can be used to bring up the docker-compose configuration:

.. code-block:: shell

    docker-compose up
