"""Import a resource from a LinkML configuration.

This curation workflow can be called from the command line by passing a URL to a LinkML
YAML configuration file like in the following:

.. code-block:: console

    $ python -m bioregistry.curation.add_linkml https://github.com/HendrikBorgelt/CatCore/blob/main/src/catcore/schema/catcore.yaml

Here are some more example LinkML YAML configuration files:

- https://github.com/HendrikBorgelt/CatCore/blob/main/src/catcore/schema/catcore.yaml
- https://github.com/mapping-commons/sssom/blob/master/src/sssom_schema/schema/sssom_schema.yaml

.. warning::

    This workflow doesn't produce complete Bioregistry records! You still must add:

    1. ``homepage``
    2. ``contributor``

    Given most LinkML configurations are on GitHub, you can probably figure out:

    - ``repository``
    - ``contact``
"""

import click
import requests
import yaml

import bioregistry

__all__ = [
    "get_resource_from_linkml",
    "import_from_linkml",
    "import_from_linkml_cli",
]


def import_from_linkml(url: str) -> None:
    """Get a resource from a LinkML configuration and write it to the registry.

    :param url: The URL to a LinkML YAML configuration file.
    :returns: A Bioregistry resource object
    """
    resource = get_resource_from_linkml(url)
    bioregistry.manager.add_resource(resource)
    bioregistry.manager.write_registry()


def get_resource_from_linkml(url: str) -> bioregistry.Resource:
    """Get a resource from a LinkML configuration.

    :param url: The URL to a LinkML YAML configuration file.
    :returns: A Bioregistry resource object
    """
    res = requests.get(url, timeout=5)
    res.raise_for_status()
    data = yaml.safe_load(res.text)

    prefix = data.pop("default_prefix")
    prefix_map = data.pop("prefixes")
    uri_prefix = prefix_map.pop(prefix)

    classes = data.pop("classes")
    first_class = next(iter(classes))

    rv = bioregistry.Resource(
        prefix=prefix,
        name=data.pop("title"),
        description=data.pop("description").replace("\n", " ").replace("  ", " "),
        license=data.pop("license", None),
        uri_format=f"{uri_prefix}$1",
        example=first_class,
        version=data.pop("version", None),
    )
    return rv


@click.command()
@click.argument("url")
def import_from_linkml_cli(url: str) -> None:
    """Add a resource from the URL."""
    import_from_linkml(url)


if __name__ == "__main__":
    import_from_linkml_cli()
