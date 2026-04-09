"""Add resources from Prefix.cc."""

from collections import defaultdict
from collections.abc import Iterable

import click
import requests
from tabulate import tabulate

import bioregistry


def main() -> None:
    """Add resources from Prefix.cc."""
    res_raw = requests.get("https://prefix.cc/context", timeout=5, verify=False)  # noqa:S501
    res = res_raw.json()["@context"]

    x = bioregistry.get_default_converter().reverse_prefix_map

    rows = []

    cc = defaultdict(set)
    for prefix, uri_prefix in res.items():
        cc[uri_prefix].add(prefix)

    for uri_prefix, prefixes in cc.items():
        if "w3.org" not in uri_prefix:
            continue
        if uri_prefix not in x:
            rows.append((", ".join(sorted(prefixes)), uri_prefix, *_xx(prefixes)))

    click.echo(tabulate(sorted(rows)))


def _xx(prefixes: Iterable[str]) -> tuple[None, None, None] | tuple[str, str | None, str | None]:
    for prefix in prefixes:
        resource = bioregistry.get_resource(prefix)
        if resource:
            return resource.prefix, resource.get_name(), resource.get_uri_prefix()
    return None, None, None


if __name__ == "__main__":
    main()
