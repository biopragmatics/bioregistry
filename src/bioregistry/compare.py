# -*- coding: utf-8 -*-

"""This script compares what's in OBO, OLS, and MIRIAM."""

import itertools as itt
import os
import sys
from collections import Counter
from typing import Collection, Set

import click

from bioregistry import read_bioregistry
from bioregistry.constants import DOCS_IMG
from bioregistry.external import get_miriam, get_n2t, get_obofoundry, get_ols, get_wikidata_registry

bioregistry = read_bioregistry()

LICENSES = {
    'None': None,
    'license': None,
    # CC-BY (4.0)
    'CC-BY 4.0': 'CC-BY',
    'CC BY 4.0': 'CC-BY',
    'https://creativecommons.org/licenses/by/4.0/': 'CC-BY',
    'http://creativecommons.org/licenses/by/4.0/': 'CC-BY',
    'http://creativecommons.org/licenses/by/4.0': 'CC-BY',
    'https://creativecommons.org/licenses/by/3.0/': 'CC-BY',
    'url: http://creativecommons.org/licenses/by/4.0/': 'CC-BY',
    'SWO is provided under a Creative Commons Attribution 4.0 International'
    ' (CC BY 4.0) license (https://creativecommons.org/licenses/by/4.0/).': 'CC-BY',
    # CC-BY (3.0)
    'CC-BY 3.0 https://creativecommons.org/licenses/by/3.0/': 'CC-BY',
    'http://creativecommons.org/licenses/by/3.0/': 'CC-BY',
    'CC-BY 3.0': 'CC-BY',
    'CC BY 3.0': 'CC-BY',
    'CC-BY version 3.0': 'CC-BY',
    # CC-BY (2.0)
    'CC-BY 2.0': 'CC-BY',
    # CC-BY (unversioned)
    'CC-BY': 'CC-BY',
    'creative-commons-attribution-license': 'CC-BY',
    # CC-BY-SA
    'CC-BY-SA': 'CC-BY-SA',
    'https://creativecommons.org/licenses/by-sa/4.0/': 'CC-BY-SA',
    # CC-BY-NC-SA
    'http://creativecommons.org/licenses/by-nc-sa/2.0/': 'CC-BY-NC-SA',
    # CC 0
    'CC-0': 'CC-0',
    'CC0 1.0 Universal': 'CC-0',
    'CC0': 'CC-0',
    'http://creativecommons.org/publicdomain/zero/1.0/': 'CC-0',
    'https://creativecommons.org/publicdomain/zero/1.0/': 'CC-0',
    # Apache 2.0
    'Apache 2.0 License': 'Other',
    'LICENSE-2.0': 'Other',
    'www.apache.org/licenses/LICENSE-2.0': 'Other',
    # Other
    'GNU GPL 3.0': 'Other',
    'hpo': 'Other',
    'Artistic License 2.0': 'Other',
    'New BSD license': 'Other',
}


def _remap_license(k):
    return k and LICENSES.get(k, k)


SINGLE_FIG = (8, 3.5)
WATERMARK_TEXT = 'https://github.com/cthoyt/bioregistry'


@click.command()
def compare():  # noqa:C901
    """Compare the registries."""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        from matplotlib_venn import venn2
    except ImportError:
        click.secho(
            'Could not import matplotlib dependencies.'
            ' Install bioregistry again with `pip install bioregistry[charts]`.',
            fg='red',
        )
        return sys.exit(1)

    watermark = True
    sns.set_style('whitegrid')

    ###############################################
    # What kinds of licenses are resources using? #
    ###############################################
    licenses = []
    conflicts = set()
    obo_has_license, ols_has_license = set(), set()
    for key, entry in bioregistry.items():
        obo_license = _remap_license(entry.get('obofoundry', {}).get('license'))
        if obo_license:
            obo_has_license.add(key)

        ols_license = _remap_license(entry.get('ols', {}).get('license'))
        if ols_license:
            ols_has_license.add(key)

        if not obo_license and not ols_license:
            licenses.append('None')
        if obo_license and not ols_license:
            licenses.append(obo_license)
        elif not obo_license and ols_license:
            licenses.append(ols_license)
        elif obo_license == ols_license:
            licenses.append(obo_license)
        else:  # different licenses!
            licenses.append(ols_license)
            licenses.append(obo_license)
            conflicts.add(key)
            print(f'[{key}] Conflicting licenses- {obo_license} and {ols_license}')
            continue

    # How many times does the license appear in OLS / OBO Foundry
    fig, ax = plt.subplots(figsize=SINGLE_FIG)
    venn2(
        subsets=(obo_has_license, ols_has_license),
        set_labels=('OBO', 'OLS'),
        set_colors=('red', 'green'),
        ax=ax,
    )
    if watermark:
        ax.text(
            0.5, -0.1, WATERMARK_TEXT, transform=plt.gca().transAxes,
            fontsize=10, color='gray', alpha=0.5,
            ha='center', va='bottom',
        )

    path = os.path.join(DOCS_IMG, 'license_coverage.png')
    click.echo(f'output to {path}')
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=SINGLE_FIG)
    sns.countplot(x=licenses, ax=ax)
    ax.set_xlabel('License')
    ax.set_ylabel('Count')
    ax.set_yscale('log')
    if watermark:
        fig.text(
            1.0, 0.5, WATERMARK_TEXT,
            fontsize=8, color='gray', alpha=0.5,
            ha='right', va='center', rotation=90,
        )

    path = os.path.join(DOCS_IMG, 'licenses.png')
    click.echo(f'output to {path}')
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    ##############################################
    # How many entries have version information? #
    ##############################################
    has_version = {
        key
        for key, entry in bioregistry.items()
        if entry.get('ols', {}).get('version')
    }
    has_pattern = {
        key
        for key, entry in bioregistry.items()
        if 'pattern' in entry or 'pattern' in entry.get('miriam', {}) or 'pattern' in entry.get('wikidata', {})
    }
    has_wikidata_database = {
        key
        for key, entry in bioregistry.items()
        if 'database' in entry.get('wikidata', {})
    }
    measurements = [
        ('Pattern', has_pattern),
        ('Version', has_version),
        ('Wikidata Database', has_wikidata_database),
    ]
    fig, axes = plt.subplots(ncols=2, nrows=(1 + len(measurements)) // 2)
    for (label, prefixes), ax in zip(measurements, axes.ravel()):
        ax.pie(
            (len(prefixes), len(bioregistry) - len(prefixes)),
            labels=('Yes', 'No'),
            autopct='%1.f%%',
            startangle=30,
            explode=[0.1, 0],
        )
        ax.set_title(f'Has {label}')
    if len(measurements) % 2:
        axes.ravel()[-1].axis('off')
    if watermark:
        fig.text(
            0.5, 0, WATERMARK_TEXT,
            fontsize=8, color='gray', alpha=0.5,
            ha='center', va='bottom',
        )

    path = os.path.join(DOCS_IMG, 'has_attribute.png')
    click.echo(f'output to {path}')
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    # -------------------------------------------------------------------- #

    miriam_prefixes = set(get_miriam(skip_deprecated=True, mappify=True))
    ols_prefixes = set(get_ols(mappify=True))
    obofoundry_prefixes = set(get_obofoundry(skip_deprecated=True, mappify=True))
    wikidata_prefixes = set(get_wikidata_registry())
    n2t_prefixes = set(get_n2t())

    keys = [
        ('obofoundry', 'OBO Foundry', 'red', obofoundry_prefixes),
        ('ols', 'OLS', 'green', ols_prefixes),
        ('miriam', 'MIRIAM', 'blue', miriam_prefixes),
        ('wikidata', 'Wikidata', 'purple', wikidata_prefixes),
        ('n2t', 'Name-to-Thing', 'orange', n2t_prefixes),
    ]

    ############################################################
    # How well does the Bioregistry cover the other resources? #
    ############################################################

    fig, axes = plt.subplots(ncols=2, nrows=(1 + len(keys)) // 2)
    for (key, label, color, prefixes), ax in zip(keys, axes.ravel()):
        # Remap bioregistry prefixes to match the external
        #  vocabulary, when possible
        bioregistry_remapped = {
            br_entry.get(key, {}).get('prefix', br_key)
            for br_key, br_entry in bioregistry.items()
        }
        venn2(
            subsets=(bioregistry_remapped, prefixes),
            set_labels=('Bioregistry', label),
            set_colors=('grey', color),
            ax=ax,
        )
    if len(keys) % 2:
        axes.ravel()[-1].axis('off')
    if watermark:
        fig.text(
            0.5, 0, WATERMARK_TEXT,
            fontsize=8, color='gray', alpha=0.5,
            ha='center', va='bottom',
        )

    path = os.path.join(DOCS_IMG, 'bioregistry_coverage.png')
    click.echo(f'output to {path}')
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    ######################################################
    # What's the overlap between each pair of resources? #
    ######################################################

    pairs = list(itt.combinations(keys, r=2))
    fig, axes = plt.subplots(ncols=2, nrows=(1 + len(pairs)) // 2)
    for ((l_key, l_label, l_color, l_prefixes), (r_key, r_label, r_color, r_prefixes)), ax in zip(pairs, axes.ravel()):
        # Remap external vocabularies to bioregistry
        #  prefixes, when possible
        l_prefixes = _remap(key=l_key, prefixes=l_prefixes)
        r_prefixes = _remap(key=r_key, prefixes=r_prefixes)
        venn2(
            subsets=(l_prefixes, r_prefixes),
            set_labels=(l_label, r_label),
            set_colors=(l_color, r_color),
            ax=ax,
        )
    if len(keys) % 2:
        axes.ravel()[-1].axis('off')
    if watermark:
        fig.text(
            0.5, 0, WATERMARK_TEXT,  # transform=plt.gca().transAxes,
            fontsize=8, color='gray', alpha=0.5,
            ha='center', va='bottom',
        )

    path = os.path.join(DOCS_IMG, 'external_overlap.png')
    click.echo(f'output to {path}')
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)

    ##############################################
    # Histogram of how many xrefs each entry has #
    ##############################################
    xref_counts = [
        sum(
            key in entry
            for key, *_ in keys
        )
        for entry in bioregistry.values()
    ]
    fig, ax = plt.subplots(figsize=SINGLE_FIG)
    sns.barplot(data=sorted(Counter(xref_counts).items()), ci=None, color='blue', alpha=0.4, ax=ax)
    ax.set_xlabel('Number External References')
    ax.set_ylabel('Count')
    ax.set_yscale('log')
    if watermark:
        fig.text(
            1.0, 0.5, WATERMARK_TEXT,
            fontsize=8, color='gray', alpha=0.5,
            ha='right', va='center', rotation=90,
        )

    path = os.path.join(DOCS_IMG, 'xrefs.png')
    click.echo(f'output to {path}')
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def _remap(*, key: str, prefixes: Collection[str]) -> Set[str]:
    br_external_to = {
        br_entry[key]['prefix']: br_id
        for br_id, br_entry in bioregistry.items()
        if key in br_entry and 'prefix' in br_entry[key]
    }
    return {
        br_external_to.get(prefix, prefix)
        for prefix in prefixes
    }


if __name__ == '__main__':
    compare()
