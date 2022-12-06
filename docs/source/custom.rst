Deploying a Custom Bioregistry
==============================
This is a tutorial on how to run a custom instance of the Bioregistry.

Vanilla Content
---------------
The Bioregistry is pushed nightly to [Docker Hub](https://hub.docker.com/r/biopragmatics/bioregistry).
You can run the latest version with:

.. code-block:: shell

    docker run -id --name bioregistry -p 8766:8766 biopragmatics/bioregistry:latest

The following script can be used to automatically update:

.. code-block shell

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
    docker run --detach --name bioregistry -p 8766:8766 biopragmatics/bioregistry:latest

Custom Content
--------------
.. todo:: how to build custom registry.json file

Dockerizing
~~~~~~~~~~~
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

Using the following two commands, the docker file can be built then
run.

.. code-block:: shell

    # Build the docker image from the same directory as the Dockerfile
    docker build --tag bioregistry_custom:latest .

    # Run the docker image, -d means "detach"
    docker run -d -p 8766:8766 bioregistry_custom:latest

Alternatively, the following `Docker compose <https://docs.docker.com/compose/>`_
configuration can be used to take care of building, tagging, and running. Put
this in the same folder as the ``Dockerfile``.

.. code-block:: yaml

    # docker-compose.yml
    version: '3'

    services:
      app:
        build: .
        restart: always
        ports:
          - "8766:8766"

The following command can be used to bring up the docker-compose configuration:

.. code-block:: shell

    docker-compose up
