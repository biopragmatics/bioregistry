# -*- coding: utf-8 -*-

"""This script compares what's in each resource."""

import datetime
import itertools as itt
import logging
import math
import random
import sys
import typing
from collections import Counter, defaultdict
from typing import Collection, List, Mapping, Set, Tuple

import click

import bioregistry
from bioregistry import (
    get_contact_email,
    get_description,
    get_example,
    get_external,
    get_homepage,
    get_json_download,
    get_license,
    get_name,
    get_obo_download,
    get_owl_download,
    get_pattern,
    get_uri_format,
    get_version,
    is_deprecated,
    manager,
    read_registry,
)
from bioregistry.constants import DOCS_IMG
from bioregistry.license_standardizer import standardize_license
from bioregistry.schema import Resource

logger = logging.getLogger(__name__)

# see named colors https://matplotlib.org/stable/gallery/color/named_colors.html
BIOREGISTRY_COLOR = "silver"


def _get_has(func, yes: str = "Yes", no: str = "No") -> Counter:
    return Counter(
        no if func(prefix) is None else yes
        for prefix in read_registry()
        if not is_deprecated(prefix)
    )


HAS_WIKIDATA_DATABASE = Counter(
    "No" if key is None else "Yes"
    for key in read_registry()
    if not is_deprecated(key) and "database" in get_external(key, "wikidata")
)


def _get_has_present(func) -> Counter:
    return Counter(x for x in (func(prefix) for prefix in read_registry()) if x)


SINGLE_FIG = (8, 3.5)
TODAY = datetime.datetime.today().strftime("%Y-%m-%d")
WATERMARK_TEXT = f"https://github.com/biopragmatics/bioregistry ({TODAY})"


def _save(fig, name: str, *, svg: bool = True, png: bool = False, eps: bool = False) -> None:
    import matplotlib.pyplot as plt

    path = DOCS_IMG.joinpath(name).with_suffix(".svg")
    click.echo(f"output to {path}")
    fig.tight_layout()
    if svg:
        fig.savefig(path)
    if eps:
        fig.savefig(DOCS_IMG.joinpath(name).with_suffix(".eps"))
    if png:
        fig.savefig(DOCS_IMG.joinpath(name).with_suffix(".png"), dpi=300)
    plt.close(fig)


def _plot_attribute_pies(*, measurements, watermark, ncols: int = 4, keep_ontology: bool = True):
    import matplotlib.pyplot as plt

    if not keep_ontology:
        measurements = [
            (label, counter)
            for label, counter in measurements
            if label not in {"OWL", "JSON", "OBO"}
        ]

    nrows = int(math.ceil(len(measurements) / ncols))
    figsize = (2.75 * ncols, 2.0 * nrows)
    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=figsize)
    for (label, counter), ax in itt.zip_longest(measurements, axes.ravel(), fillvalue=(None, None)):
        if label is None:
            ax.axis("off")
            continue
        if label == "License Type":
            labels, sizes = zip(*counter.most_common())
            explode = None
        else:
            labels = ("Yes", "No")
            n_yes = counter.get("Yes")
            sizes = (n_yes, len(read_registry()) - n_yes)
            explode = [0.1, 0]
        ax.pie(
            sizes,
            labels=labels,
            autopct="%1.f%%",
            startangle=30,
            explode=explode,
        )
        ax.set_title(label)
    if watermark:
        fig.text(
            0.5,
            0,
            WATERMARK_TEXT,
            fontsize=8,
            color="gray",
            alpha=0.5,
            ha="center",
            va="bottom",
        )
    return fig, axes


REMAPPED_KEY = "x"
REMAPPED_VALUE = "y"


def make_overlaps(keys) -> Mapping[str, Mapping[str, Set[str]]]:
    """Make overlaps ditionary."""
    rv = {}
    for key, _, _, prefixes in keys:
        # Remap bioregistry prefixes to match the external
        #  vocabulary, when possible
        bioregistry_remapped = {
            bioregistry.get_external(br_key, key).get("prefix", br_key)
            for br_key, br_entry in bioregistry.read_registry().items()
        }
        rv[key] = {
            REMAPPED_KEY: bioregistry_remapped,
            REMAPPED_VALUE: prefixes,
        }
    return rv


def _plot_coverage(*, keys, overlaps, watermark, ncols: int = 3):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2

    nrows = int(math.ceil(len(keys) / ncols))
    figsize = (3.25 * ncols, 2.0 * nrows)
    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=figsize)

    for key, ax in itt.zip_longest(keys, axes.ravel()):
        if key is None:
            ax.axis("off")
            continue
        key, label, color, prefixes = key
        bioregistry_remapped = overlaps[key][REMAPPED_KEY]
        venn2(
            subsets=(bioregistry_remapped, prefixes),
            set_labels=("Bioregistry", label),
            set_colors=(BIOREGISTRY_COLOR, color),
            ax=ax,
        )
    if watermark:
        fig.text(
            0.5,
            0,
            WATERMARK_TEXT,
            fontsize=8,
            color="gray",
            alpha=0.5,
            ha="center",
            va="bottom",
        )
    return fig, axes


def _plot_external_overlap(*, keys, watermark, ncols: int = 4):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2

    pairs = list(itt.combinations(keys, r=2))
    nrows = int(math.ceil(len(pairs) / ncols))
    figsize = (3 * ncols, 2.5 * nrows)
    fig, axes = plt.subplots(ncols=ncols, nrows=nrows, figsize=figsize)
    for pair, ax in itt.zip_longest(pairs, axes.ravel()):
        if pair is None:
            ax.axis("off")
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
            0.5,
            0,
            WATERMARK_TEXT,  # transform=plt.gca().transAxes,
            fontsize=14,
            color="gray",
            alpha=0.5,
            ha="center",
            va="bottom",
        )
    return fig, axes


def get_getters():
    """Get getter functions, which requires alignment dependencies."""
    try:
        from bioregistry.external import GETTERS
    except ImportError:
        click.secho(
            "Could not import alignment dependencies."
            " Install bioregistry again with `pip install bioregistry[align]`.",
            fg="red",
        )
        return sys.exit(1)
    else:
        return GETTERS


def get_keys() -> List[Tuple[str, str, str, Set[str]]]:
    """Get keys for plots."""
    getters = get_getters()
    try:
        import seaborn as sns
    except ImportError:
        raise
    else:
        palette = sns.color_palette("Paired", len(getters))
    return [
        (metaprefix, label, color, set(func(force_download=False)))
        for (metaprefix, label, func), color in zip(getters, palette)
    ]


@click.command()
@click.option("--paper", is_flag=True)
def compare(paper: bool):  # noqa:C901
    """Compare the registries."""
    paper = True
    random.seed(0)
    try:
        import matplotlib.pyplot as plt
        import pandas as pd
        import seaborn as sns
    except ImportError:
        click.secho(
            "Could not import matplotlib dependencies."
            " Install bioregistry again with `pip install bioregistry[charts]`.",
            fg="red",
        )
        return sys.exit(1)

    keys = get_keys()
    overlaps = make_overlaps(keys)

    # This should make SVG output deterministic
    # See https://matplotlib.org/3.1.0/users/prev_whats_new/whats_new_2.0.0.html#added-svg-hashsalt-key-to-rcparams
    plt.rcParams["svg.hashsalt"] = "saltyregistry"

    watermark = True
    sns.set_style("white")

    ###############################################
    # What kinds of licenses are resources using? #
    ###############################################
    licenses, conflicts, obo_has_license, ols_has_license = _get_license_and_conflicts()

    # How many times does the license appear in OLS / OBO Foundry
    # fig, ax = plt.subplots(figsize=SINGLE_FIG)
    # venn2(
    #     subsets=(obo_has_license, ols_has_license),
    #     set_labels=("OBO", "OLS"),
    #     set_colors=("red", "green"),
    #     ax=ax,
    # )
    # if watermark:
    #     ax.text(
    #         0.5,
    #         -0.1,
    #         WATERMARK_TEXT,
    #         transform=plt.gca().transAxes,
    #         fontsize=10,
    #         color="gray",
    #         alpha=0.5,
    #         ha="center",
    #         va="bottom",
    #     )
    # _save(fig, name="license_coverage", eps=paper)

    fig, ax = plt.subplots(figsize=SINGLE_FIG)
    licenses_counter: typing.Counter[str] = Counter(licenses)
    licenses_mapped = [
        "None" if license_ is None else license_ if licenses_counter[license_] > 30 else "Other"
        for license_ in licenses
    ]
    licenses_mapped_counter = Counter(licenses_mapped)
    licenses_mapped_order = [license_ for license_, _ in licenses_mapped_counter.most_common()]
    sns.countplot(x=licenses_mapped, ax=ax, order=licenses_mapped_order)
    ax.set_xlabel("License")
    ax.set_ylabel("Count")
    ax.set_yscale("log")
    if watermark:
        fig.text(
            1.0,
            0.5,
            WATERMARK_TEXT,
            fontsize=8,
            color="gray",
            alpha=0.5,
            ha="right",
            va="center",
            rotation=90,
        )
    _save(fig, name="licenses", eps=paper)

    ##############################################
    # How many entries have version information? #
    ##############################################
    measurements = [
        ("Name", _get_has(get_name)),
        ("Homepage", _get_has(get_homepage)),
        ("Description", _get_has(get_description)),
        ("Example", _get_has(get_example)),
        ("Pattern", _get_has(get_pattern)),
        ("Provider", _get_has(get_uri_format)),
        ("License", _get_has(get_license)),
        ("License Type", _get_has_present(get_license)),
        ("Version", _get_has(get_version)),
        ("Contact Email", _get_has(get_contact_email)),
        ("Wikidata Database", HAS_WIKIDATA_DATABASE),
        ("OBO", _get_has(get_obo_download)),
        ("OWL", _get_has(get_owl_download)),
        ("JSON", _get_has(get_json_download)),
    ]

    fig, axes = _plot_attribute_pies(measurements=measurements, watermark=watermark)
    _save(fig, "has_attribute", eps=paper)

    # Slightly reorganized for the paper
    if paper:
        fig, axes = _plot_attribute_pies(
            measurements=measurements, watermark=watermark, keep_ontology=False
        )
        _save(fig, "paper_figure_3", png=True, eps=True)

    # -------------------------------------------------------------------- #

    ############################################################
    # How well does the Bioregistry cover the other resources? #
    ############################################################
    fig, axes = _plot_coverage(keys=keys, overlaps=overlaps, watermark=watermark)
    _save(fig, name="bioregistry_coverage", eps=paper)
    plot_coverage_bar_abridged(overlaps=overlaps, paper=paper)
    plot_coverage_bar(overlaps=overlaps, paper=True)

    ######################################################
    # What's the overlap between each pair of resources? #
    ######################################################
    fig, axes = _plot_external_overlap(keys=keys, watermark=watermark)
    _save(fig, name="external_overlap", eps=paper)

    ##############################################
    # Histogram of how many xrefs each entry has #
    ##############################################
    xref_counts = [
        sum(0 < len(entry.get_external(key)) for key, *_ in keys)
        for entry in read_registry().values()
    ]
    fig, ax = plt.subplots(figsize=SINGLE_FIG)
    xrefs_counter: typing.Counter[int] = Counter(xref_counts)

    n_mappable_metaprefixes = len(
        {
            metaprefix
            for entry in read_registry().values()
            for metaprefix in (entry.get_mappings() or {})
        }
    )
    zero_pad_count = 0  # how many columns left from the end should it go
    for i in range(n_mappable_metaprefixes):
        if i not in xrefs_counter:
            zero_pad_count += 1
            xrefs_counter[i] = 0

    xrefs_df = pd.DataFrame(sorted(xrefs_counter.items()), columns=["frequency", "count"])
    palette = sns.color_palette("tab10")
    xrefs_colors = [palette[2]] + ([palette[1]] * (len(xrefs_df.index) - 1))
    sns.barplot(
        data=xrefs_df,
        x="frequency",
        y="count",
        ci=None,
        palette=xrefs_colors,
        alpha=1.0,
        ax=ax,
    )
    # There should only be one container here
    _labels = xrefs_df["count"].to_list()
    _labels[0] = f"{_labels[0]}\nNovel"
    for i in ax.containers:
        ax.bar_label(i, _labels)
    ax.set_xlabel("Number Cross-Registry Mappings")
    ax.set_ylabel("Number Prefixes")
    ax.set_yscale("log")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    h = 15  # how high should the text go
    x1, _y1 = ax.patches[-zero_pad_count].get_xy()
    x2, _y2 = ax.patches[-1].get_xy()
    ax.text(
        x1,
        h + 1,
        "No prefixes are available\nin $\\it{all}$ mappable external\nregistries",
        horizontalalignment="center",
        verticalalignment="bottom",
        fontdict=dict(fontsize=12),
    )
    ax.arrow(x1, h, x2 - x1, 2 - h, head_width=0.3, head_length=0.2, fc="k", ec="k")
    if watermark:
        fig.text(
            1.0,
            0.5,
            WATERMARK_TEXT,
            fontsize=8,
            color="gray",
            alpha=0.5,
            ha="right",
            va="center",
            rotation=90,
        )

    offset = 0.6
    ax.set_xlim([-offset, len(ax.patches) - (1 + offset)])
    _save(fig, name="xrefs", eps=paper, png=paper)

    ##################################################
    # Histogram of how many providers each entry has #
    ##################################################
    provider_counts = [_count_providers(resource) for resource in read_registry().values()]
    fig, ax = plt.subplots(figsize=SINGLE_FIG)
    sns.barplot(
        data=sorted(Counter(provider_counts).items()), ci=None, color="blue", alpha=0.4, ax=ax
    )
    ax.set_xlabel("Number Providers")
    ax.set_ylabel("Count")
    ax.set_yscale("log")
    if watermark:
        fig.text(
            1.0,
            0.5,
            WATERMARK_TEXT,
            fontsize=8,
            color="gray",
            alpha=0.5,
            ha="right",
            va="center",
            rotation=90,
        )
    _save(fig, name="providers", eps=paper)

    ########################################
    # Regular expression complexity report #
    ########################################
    g = sns.displot(x=get_regex_complexities(), log_scale=2, height=3, aspect=4 / 3)
    g.set(xlabel="Regular Expression Complexity")
    _save(g.figure, name="regex_report", eps=paper)


def _count_providers(resource: Resource) -> int:
    rv = 0
    if resource.get_uri_prefix():
        rv += 1
    rv += len(resource.get_extra_providers())
    return rv


def _get_license_and_conflicts():
    licenses = []
    conflicts = set()
    obo_has_license, ols_has_license = set(), set()
    for key in read_registry():
        obo_license = standardize_license(get_external(key, "obofoundry").get("license"))
        if obo_license:
            obo_has_license.add(key)

        ols_license = standardize_license(get_external(key, "ols").get("license"))
        if ols_license:
            ols_has_license.add(key)

        if not obo_license and not ols_license:
            licenses.append("None")
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
            # logger.warning(f"[{key}] Conflicting licenses- {obo_license} and {ols_license}")
            continue
    return licenses, conflicts, obo_has_license, ols_has_license


def _remap(*, key: str, prefixes: Collection[str]) -> Set[str]:
    br_external_to = {}
    for br_id, resource in read_registry().items():
        _k = (resource.dict().get(key) or {}).get("prefix")
        if _k:
            br_external_to[_k] = br_id

    return {br_external_to.get(prefix, prefix) for prefix in prefixes}


def get_regex_complexities() -> Collection[float]:
    """Get a list of regular expression complexities."""
    rows = []
    for prefix in manager.registry:
        pattern = manager.get_pattern(prefix)
        if pattern is None:
            continue
        # Consider alternate complexity estimates
        rows.append(float(len(pattern)))
    return sorted(rows)


def plot_coverage_bar_abridged(*, overlaps, paper: bool = False):
    """Plot and save the abridged coverage bar chart."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    sns.set_style("white")

    rows = []
    for metaprefix, data in overlaps.items():
        br, external = data[REMAPPED_KEY], data[REMAPPED_VALUE]
        rows.append(
            (
                bioregistry.get_registry_short_name(metaprefix),
                len(external - br),
                len(br.intersection(external)),
            )
        )
    rows = sorted(rows, key=lambda row: sum(row[1:]), reverse=True)

    df2 = pd.DataFrame(rows, columns=["metaprefix", "external_only", "intersection"])
    df2.set_index("metaprefix", inplace=True)

    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    df2.plot(
        kind="barh",
        stacked=True,
        ax=ax,
        width=0.85,
        fontsize=14,
        grid=False,
    )
    ax.grid(False)
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(
        top=False, bottom=False, left=False, right=False, labelleft=True, labelbottom=False
    )

    dd = defaultdict(list)
    for p in ax.patches:
        width, height = p.get_width(), p.get_height()
        x, y = p.get_xy()
        dd[y, height].append((width, x))
        if width < 20:
            continue
        ax.text(
            x + width / 2,
            y + height / 2,
            f"{int(width):,}",
            horizontalalignment="center",
            verticalalignment="center",
            fontdict=dict(weight="bold", color="white", fontsize=12),
        )

    for (y, height), values in dd.items():
        width_total = sum(int(w) for w, _ in values)
        percentage = values[-1][0] / width_total
        width, x = max(values, key=lambda item: item[1])
        ax.text(
            width + x + 20,
            y + height / 2,
            f"{percentage:.1%} coverage",
            fontdict=dict(weight="normal", color="black", fontsize=12),
            verticalalignment="center",
        )

    ax.get_legend().remove()
    plt.tight_layout()
    _save(fig, name="bioregistry_coverage_bar_short", eps=paper)


def plot_coverage_bar(*, overlaps, paper: bool = False):
    """Plot and save the coverage bar chart."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    sns.set_style("white")

    rows_1 = []
    for metaprefix, data in overlaps.items():
        br, external = data[REMAPPED_KEY], data[REMAPPED_VALUE]
        rows_1.append(
            (
                bioregistry.get_registry_short_name(metaprefix),
                len(external - br),
                len(br.intersection(external)),
                len(br - external),
            )
        )
    rows_1 = sorted(rows_1, key=lambda row: sum(row[1:]), reverse=True)

    df1 = pd.DataFrame(
        rows_1, columns=["metaprefix", "external_only", "intersection", "bioregistry_only"]
    )
    df1.set_index("metaprefix", inplace=True)

    fig, ax = plt.subplots(1, 1, figsize=(10, 7))
    df1.plot(
        kind="barh",
        stacked=True,
        ax=ax,
        width=0.85,
        fontsize=14,
        grid=False,
    )
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(
        top=False, bottom=False, left=False, right=False, labelleft=True, labelbottom=False
    )

    dd = defaultdict(list)
    for p in ax.patches:
        width, height = p.get_width(), p.get_height()
        x, y = p.get_xy()
        dd[y, height].append((width, x))
        if width < 40:
            continue
        ax.text(
            x + width / 2,
            y + height / 2,
            f"{int(width):,}",
            horizontalalignment="center",
            verticalalignment="center",
            fontdict=dict(weight="bold", color="white", fontsize=12),
        )

    for (y, height), values in dd.items():
        width_total = sum(int(w) for w, _ in values)
        without_br = sum(int(w) for w, _ in values[:-1])
        increase = (width_total - without_br) / without_br
        width, x = max(values, key=lambda item: item[1])
        ax.text(
            width + x + 20,
            y + height / 2,
            f"{int(width_total):,} (+{increase:,.0%})",
            fontdict=dict(weight="normal", color="black", fontsize=12),
            verticalalignment="center",
        )

    for label in ax.get_yticklabels():
        label.set_fontweight("bold")

    ax.get_legend().remove()
    plt.tight_layout()
    _save(fig, name="bioregistry_coverage_bar", eps=paper, png=True)


if __name__ == "__main__":
    compare()
