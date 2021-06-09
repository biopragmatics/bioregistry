# -*- coding: utf-8 -*-

"""This script compares what's in each resource."""

import datetime
import itertools as itt
import math
import random
import sys
from collections import Counter
from typing import Collection, Set

import click

from bioregistry import (
    get_description, get_email, get_example, get_format, get_homepage, get_json_download, get_name, get_obo_download,
    get_owl_download, get_pattern, get_version, read_registry,
)
from bioregistry.constants import DOCS_IMG
from bioregistry.external import GETTERS
from bioregistry.resolve import get_external

LICENSES = {
    'None': None,
    'license': None,
    'unspecified': None,
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

# see named colors https://matplotlib.org/stable/gallery/color/named_colors.html
BIOREGISTRY_COLOR = 'silver'


def _get_has(f):
    return {key for key in read_registry() if f(key)}


HAS_WIKIDATA_DATABASE = {
    key
    for key in read_registry()
    if 'database' in get_external(key, 'wikidata')
}


def _remap_license(k):
    return k and LICENSES.get(k, k)


SINGLE_FIG = (8, 3.5)
TODAY = datetime.datetime.today().strftime('%Y-%m-%d')
WATERMARK_TEXT = f'https://github.com/bioregistry/bioregistry ({TODAY})'


def _save(fig, name: str, *, png: bool = False) -> None:
    import matplotlib.pyplot as plt
    path = DOCS_IMG.joinpath(name).with_suffix('.svg')
    click.echo(f'output to {path}')
    fig.tight_layout()
    fig.savefig(path)
    if png:
        fig.savefig(DOCS_IMG.joinpath(name).with_suffix('.png'), dpi=300)
    plt.close(fig)


def _plot_attribute_pies(*, measurements, watermark):
    import matplotlib.pyplot as plt
    ncols = 3
    nrows = int(math.ceil(len(measurements) / ncols))
    fig, axes = plt.subplots(ncols=ncols, nrows=nrows)
    for measurement, ax in itt.zip_longest(measurements, axes.ravel()):
        if measurement is None:
            ax.axis('off')
            continue
        label, prefixes = measurement
        ax.pie(
            (len(prefixes), len(read_registry()) - len(prefixes)),
            labels=('Yes', 'No'),
            autopct='%1.f%%',
            startangle=30,
            explode=[0.1, 0],
        )
        ax.set_title(label)
    if watermark:
        fig.text(
            0.5, 0, WATERMARK_TEXT,
            fontsize=8, color='gray', alpha=0.5,
            ha='center', va='bottom',
        )
    return fig, axes


def _plot_coverage(*, keys, watermark):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2
    ncols = 3
    nrows = int(math.ceil(len(keys) / ncols))
    figsize = (3.25 * ncols, 2.0 * nrows)
    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=figsize)
    for key, ax in itt.zip_longest(keys, axes.ravel()):
        if key is None:
            ax.axis('off')
            continue
        key, label, color, prefixes = key
        # Remap bioregistry prefixes to match the external
        #  vocabulary, when possible
        bioregistry_remapped = {
            get_external(br_key, key).get('prefix', br_key)
            for br_key, br_entry in read_registry().items()
        }
        venn2(
            subsets=(bioregistry_remapped, prefixes),
            set_labels=('Bioregistry', label),
            set_colors=(BIOREGISTRY_COLOR, color),
            ax=ax,
        )
    if watermark:
        fig.text(
            0.5, 0, WATERMARK_TEXT,
            fontsize=8, color='gray', alpha=0.5,
            ha='center', va='bottom',
        )
    return fig, axes


def _plot_external_overlap(*, keys, watermark):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2
    pairs = list(itt.combinations(keys, r=2))
    ncols = 4
    nrows = int(math.ceil(len(pairs) / ncols))
    figsize = (3 * ncols, 2.5 * nrows)
    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=figsize)
    for pair, ax in itt.zip_longest(pairs, axes.ravel()):
        if pair is None:
            ax.axis('off')
            continue
        (l_key, l_label, l_color, l_prefixes), (r_key, r_label, r_color, r_prefixes) = pair
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
    if watermark:
        fig.text(
            0.5, 0, WATERMARK_TEXT,  # transform=plt.gca().transAxes,
            fontsize=14, color='gray', alpha=0.5,
            ha='center', va='bottom',
        )
    return fig, axes


@click.command()
@click.option('--png', is_flag=True)
def compare(png: bool):  # noqa:C901
    """Compare the registries."""
    random.seed(0)
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

    # This should make SVG output deterministic
    plt.rcParams['svg.hashsalt'] = 'saltyregistry'

    watermark = True
    sns.set_style('whitegrid')

    ###############################################
    # What kinds of licenses are resources using? #
    ###############################################
    licenses, conflicts, obo_has_license, ols_has_license = _get_license_and_conflicts()

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
    _save(fig, name='license_coverage', png=png)

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
    _save(fig, name='licenses', png=png)

    ##############################################
    # How many entries have version information? #
    ##############################################
    measurements = [
        ('Name', _get_has(get_name)),
        ('Description', _get_has(get_description)),
        ('Version', _get_has(get_version)),
        ('Homepage', _get_has(get_homepage)),
        ('Contact Email', _get_has(get_email)),
        ('Pattern', _get_has(get_pattern)),
        ('Format URL', _get_has(get_format)),
        ('Example', _get_has(get_example)),
        ('Wikidata Database', HAS_WIKIDATA_DATABASE),
        ('OBO', _get_has(get_obo_download)),
        ('OWL', _get_has(get_owl_download)),
        ('JSON', _get_has(get_json_download)),
    ]

    fig, axes = _plot_attribute_pies(measurements=measurements, watermark=watermark)
    _save(fig, 'has_attribute', png=png)

    # -------------------------------------------------------------------- #
    palette = sns.color_palette("Paired", len(GETTERS))
    keys = [
        (metaprefix, label, color, set(func()))
        for (metaprefix, label, func), color in zip(GETTERS, palette)
    ]

    ############################################################
    # How well does the Bioregistry cover the other resources? #
    ############################################################
    fig, axes = _plot_coverage(keys=keys, watermark=watermark)
    _save(fig, name='bioregistry_coverage', png=png)

    ######################################################
    # What's the overlap between each pair of resources? #
    ######################################################
    fig, axes = _plot_external_overlap(keys=keys, watermark=watermark)
    _save(fig, name='external_overlap', png=png)

    ##############################################
    # Histogram of how many xrefs each entry has #
    ##############################################
    xref_counts = [
        sum(
            0 < len(entry.get_external(key))
            for key, *_ in keys
        )
        for entry in read_registry().values()
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

    _save(fig, name='xrefs', png=png)


def _get_license_and_conflicts():
    licenses = []
    conflicts = set()
    obo_has_license, ols_has_license = set(), set()
    for key in read_registry():
        obo_license = _remap_license(get_external(key, 'obofoundry').get('license'))
        if obo_license:
            obo_has_license.add(key)

        ols_license = _remap_license(get_external(key, 'ols').get('license'))
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
    return licenses, conflicts, obo_has_license, ols_has_license


def _remap(*, key: str, prefixes: Collection[str]) -> Set[str]:
    br_external_to = {}
    for br_id, resource in read_registry().items():
        _k = (resource.dict().get(key) or {}).get('prefix')
        if _k:
            br_external_to[_k] = br_id

    return {
        br_external_to.get(prefix, prefix)
        for prefix in prefixes
    }


if __name__ == '__main__':
    compare()
