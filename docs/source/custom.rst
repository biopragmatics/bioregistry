Deploying a Custom Bioregistry
==============================
This is a tutorial on how to run a custom instance of the Bioregistry.

Vanilla Content
---------------
The Bioregistry is pushed nightly to docker. You can run the latest version with

.. code-block:: shell

    docker run -id --name bioregistry -p 8766:8766 biopragmatics/bioregistry:latest

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
