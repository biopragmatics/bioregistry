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
from bioregistry.utils import _norm

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


GITHUB_URL_PREFIX = "https://github.com/"


def _fix_github(url: str) -> str:
    """Fix copy-pasted GitHub URLs.

    >>> _fix_github(
    ...     "https://github.com/ghga-de/ghga-metadata-schema/blob/main/src/schema/submission.yaml"
    ... )
    'https://github.com/ghga-de/ghga-metadata-schema/raw/refs/heads/main/src/schema/submission.yaml'
    """
    if url.startswith(GITHUB_URL_PREFIX) and "/blob/" in url:
        url = url.split("#")[0]  # strip off any anchors
        url = url.replace("/blob/", "/raw/refs/heads/")
    return url


def _extract_repository(url: str) -> str | None:
    """Extract a GitHub repository URL from a file URL.

     >>> _extract_repository(
    ...     "https://github.com/ghga-de/ghga-metadata-schema/blob/main/src/schema/submission.yaml"
    ... )
    'https://github.com/ghga-de/ghga-metadata-schema'
    """
    if url.startswith(GITHUB_URL_PREFIX):
        parts = url[len(GITHUB_URL_PREFIX) :].split("/")
        return GITHUB_URL_PREFIX + "/".join(parts[:2])
    return None


def get_resource_from_linkml(url: str) -> bioregistry.Resource:
    """Get a resource from a LinkML configuration.

    :param url: The URL to a LinkML YAML configuration file.
    :returns: A Bioregistry resource object
    """
    res = requests.get(_fix_github(url), timeout=5)
    res.raise_for_status()
    data = yaml.safe_load(res.text)

    preferred_prefix = data.pop("default_prefix")
    prefix_map = data.pop("prefixes")
    uri_prefix = prefix_map.pop(preferred_prefix)

    classes = data.pop("classes")
    first_class = next(iter(classes))

    # prefix is case normalized
    prefix = _norm(preferred_prefix)

    rv = bioregistry.Resource(
        prefix=prefix,
        preferred_prefix=preferred_prefix,
        name=data.get("title") or data.get("name"),
        description=data.pop("description").replace("\n", " ").replace("  ", " "),
        license=data.pop("license", None),
        uri_format=f"{uri_prefix}$1",
        example=first_class,
        version=data.pop("version", None),
        homepage=data.pop("id", None),
        repository=_extract_repository(url),
        domain="schema",
    )
    return rv


@click.command()
@click.argument("url")
def import_from_linkml_cli(url: str) -> None:
    """Add a resource from the URL."""
    import_from_linkml(url)


if __name__ == "__main__":
    import_from_linkml_cli()
