# -*- coding: utf-8 -*-

"""This script compares what's in OBO, OLS, and MIRIAM."""

import itertools as itt
import os

import click
import matplotlib.pyplot as plt
from matplotlib_venn import venn3

from bioregistry import read_bioregistry
from bioregistry.constants import DOCS
from bioregistry.external import get_miriam, get_obofoundry, get_ols, get_wikidata_registry


@click.command()
def compare():
    """Compare the registries."""
    bioregistry = read_bioregistry()
    bioregistry_entries = set(bioregistry)

    miriam = get_miriam(skip_deprecated=True)
    miriam_entries = {
        entry['prefix'].lower()
        for entry in miriam
    }

    ols = get_ols()
    ols_entries = {
        entry['ontologyId'].lower()
        for entry in ols
    }

    obofoundry = get_obofoundry(skip_deprecated=True)
    obofoundry_entries = {
        entry['id'].lower()
        for entry in obofoundry
    }

    wikidata = get_wikidata_registry()

    keys = [
        ('OBO Foundry', 'g', obofoundry_entries),
        ('OLS', 'y', ols_entries),
        ('MIRIAM', 'b', miriam_entries),
        ('WikiData', 'purple', wikidata),
    ]
    combinations = list(itt.combinations(keys, 2))
    fig, axes = plt.subplots(ncols=2, nrows=len(combinations) // 2)
    for ((x_label, x_color, x), (y_label, y_color, y)), ax in zip(combinations, axes.ravel()):
        venn3(
            subsets=[bioregistry_entries, x, y],
            set_colors=('r', x_color, y_color),
            set_labels=('Bioregistry', x_label, y_label),
            ax=ax,
        )

    plt.tight_layout()
    directory = os.path.join(DOCS, 'img')
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, 'comparison.png')
    print('output to', path)
    plt.savefig(path, dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    compare()
