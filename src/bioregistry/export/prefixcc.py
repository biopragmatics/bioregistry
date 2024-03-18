"""Update Prefix.cc to reflect the content of the Bioregistry.

.. seealso:: https://github.com/OBOFoundry/OBOFoundry.github.io/issues/1038
"""

import click
import requests

import bioregistry


def create(curie_prefix: str, uri_prefix: str) -> requests.Response:
    """Send a CURIE prefix/URI prefix to the Prefix.cc "create" endpoint."""
    return requests.post(
        f"https://prefix.cc/{curie_prefix}",
        data={"create": uri_prefix},
    )


def main():
    """Add an OBO Foundry prefix to Prefix.cc."""
    prefix_cc_map = requests.get("https://prefix.cc/context").json()["@context"]
    for record in bioregistry.resources():
        if not record.get_obofoundry_prefix():
            continue
        uri_prefix = record.get_uri_prefix()
        if not uri_prefix:
            continue
        if uri_prefix == prefix_cc_map.get(record.prefix):
            # No need to re-create something that's already
            # both available and correct wrt Bioregistry/OBO
            continue

        click.echo(f"Attempting to create a record for {record.prefix} {uri_prefix}")
        res = create(record.prefix, uri_prefix)
        click.echo(res.text)

        # We're breaking here since we can only make one
        # update per day
        break


if __name__ == "__main__":
    main()
