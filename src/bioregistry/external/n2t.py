# -*- coding: utf-8 -*-

"""Download registry information from N2T."""

import itertools as itt
from operator import itemgetter

import click
import pystow
import yaml
from more_itertools import pairwise


URL = 'https://n2t.net/e/cdl_ebi_prefixes.yaml'

PATH = pystow.join('bioregistry', name='n2t.json')


def _parse_1(file):
    lines = (
        line.strip()
        for line in file
        if not line.startswith('#') and line.strip()
    )
    it = itt.groupby(lines, lambda line: line.startswith('-'))
    for a, grouped_lines in it:
        if a:
            k, v = [part.strip() for part in list(grouped_lines)[0].lstrip('-').lstrip().split(':', 1)]
            yield [(k, v)]
        else:
            yield [
                [part.strip() for part in line.split(':', 1)]
                for line in grouped_lines
            ]


def _parse(file):
    for a, b in pairwise(_parse_1(file)):
        yield dict(itt.chain(a, b))


def get_n2t():
    """Get the N2T registry."""
    path = pystow.ensure('bioregistry', url=URL)
    # they give malformed YAML so time to write a new parser
    with open(path) as file:
        rv = sorted(_parse(file), key=itemgetter('namespace'))

    nrv = {
        prefix: _clean_providers(lines)
        for prefix, lines in itt.groupby(rv, key=itemgetter('namespace'))
    }

    with PATH.open('w') as file:
        yaml.dump(nrv, file)
    return nrv


def _clean_providers(lines):
    providers = list(lines)
    for provider in providers:
        del provider['namespace']
    return providers


@click.command()
def main():
    """Reload the N2T data."""
    get_n2t()


if __name__ == '__main__':
    main()
