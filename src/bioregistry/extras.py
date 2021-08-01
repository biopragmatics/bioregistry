# -*- coding: utf-8 -*-

"""Extra getters."""

from collections import defaultdict

from typing import Mapping, Set, Tuple

from bioregistry.schema import Author
from bioregistry.utils import read_registry

__all__ = [
    'get_contributors',
]


def get_contributors() -> Mapping[str, Tuple[Author, Set[str]]]:
    """Get contributors."""
    om = {}
    dd = defaultdict(set)
    for prefix, resource in read_registry().items():
        if resource.contributor:
            om[resource.contributor.orcid] = resource.contributor
            dd[resource.contributor.orcid].add(prefix)
    return {
        orcid: (contributor, dd[orcid])
        for orcid, contributor in om.items()
    }


if __name__ == '__main__':
    from tabulate import tabulate

    print(tabulate(headers=["ORCID", "Name", "Email", "Contributions"], tabular_data=[
        (author.orcid, author.name, author.email, len(prefixes))
        for author, prefixes in get_contributors().values()
    ]))
