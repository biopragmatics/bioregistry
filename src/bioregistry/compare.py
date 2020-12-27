# -*- coding: utf-8 -*-

"""This script compares what's in OBO, OLS, and MIRIAM."""

import itertools as itt
import os

import click
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3

from bioregistry import read_bioregistry
from bioregistry.constants import DOCS
from bioregistry.external import get_miriam, get_n2t, get_obofoundry, get_ols, get_wikidata_registry


@click.command()
def compare():
    """Compare the registries."""
    directory = os.path.join(DOCS, 'img')
    os.makedirs(directory, exist_ok=True)

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

    n2t_entries = set(get_n2t())

    # MIRIAM vs. N2T
    print('in n2t but not miriam')
    for x in n2t_entries - miriam_entries:
        print(x)

    fig, axes = plt.subplots(ncols=2)
    venn2(
        subsets=[miriam_entries, n2t_entries],
        set_labels=['MIRIAM', 'N2T'],
        ax=axes[0],
    )
    venn2(
        subsets=[obofoundry_entries, ols_entries],
        set_labels=['OBO Foundry', 'OLS'],
        ax=axes[1],
    )
    path = os.path.join(directory, 'comparison_1_way.png')
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)

    keys = [
        ('OBO Foundry', 'g', obofoundry_entries),
        ('OLS', 'y', ols_entries),
        ('MIRIAM', 'b', miriam_entries),
        ('Wikidata', 'purple', wikidata),
    ]

    # 2-way
    keys_2_way = [*keys, ('N2T', 'grey', n2t_entries)]
    fig, axes = plt.subplots(ncols=2, nrows=(1 + len(keys_2_way)) // 2)
    for (label, color, subset), ax in zip(keys_2_way, axes.ravel()):
        venn2(
            subsets=(bioregistry_entries, subset),
            set_labels=('Bioregistry', label),
            set_colors=('r', color),
            ax=ax,
        )
    if len(keys_2_way) % 2:
        axes.ravel()[-1].axis('off')

    path = os.path.join(directory, 'comparison_2_way.png')
    print('output to', path)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)

    # 3-way
    combinations = list(itt.combinations(keys, 2))
    fig, axes = plt.subplots(ncols=2, nrows=len(combinations) // 2)
    for ((x_label, x_color, x), (y_label, y_color, y)), ax in zip(combinations, axes.ravel()):
        venn3(
            subsets=[bioregistry_entries, x, y],
            set_colors=('r', x_color, y_color),
            set_labels=('Bioregistry', x_label, y_label),
            ax=ax,
        )

    path = os.path.join(directory, 'comparison.png')
    print('output to', path)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    compare()
