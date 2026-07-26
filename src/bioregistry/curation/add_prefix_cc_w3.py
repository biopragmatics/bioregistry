"""Add resources from Prefix.cc."""

from collections import defaultdict
from collections.abc import Iterable

import click
import requests
from tabulate import tabulate

import bioregistry

SKIP_CC_URI_PREFIXES = {
    "http://www.w3.org/",
    "http://www.w3.org/XML/1998/namespace/",  # incorrectly ends with /
}


def main() -> None:
    """Add resources from Prefix.cc."""
    res_raw = requests.get("https://prefix.cc/context", timeout=5, verify=False)  # noqa:S501
    res = res_raw.json()["@context"]

    uri_prefix_to_prefix = bioregistry.get_default_converter().reverse_prefix_map

    cc = defaultdict(set)
    for prefix, uri_prefix in res.items():
        cc[uri_prefix].add(prefix)

    rows = []
    for uri_prefix, curie_prefixes in cc.items():
        if (
            "w3.org" not in uri_prefix
            or uri_prefix in uri_prefix_to_prefix
            or uri_prefix in SKIP_CC_URI_PREFIXES
        ):
            continue
        rows.append((", ".join(sorted(curie_prefixes)), uri_prefix, *_xx(curie_prefixes)))

    click.echo(tabulate(sorted(rows)))


def _xx(prefixes: Iterable[str]) -> tuple[None, None, None] | tuple[str, str | None, str | None]:
    for prefix in prefixes:
        resource = bioregistry.get_resource(prefix)
        if resource:
            return resource.prefix, resource.get_name(), resource.get_uri_prefix()
    return None, None, None


if __name__ == "__main__":
    main()
