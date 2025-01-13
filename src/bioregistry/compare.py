"""This script compares what's in each resource."""

from __future__ import annotations

import datetime
import itertools as itt
import logging
import math
import random
import sys
import typing
from collections import Counter, defaultdict
from collections.abc import Collection, Mapping
from typing import TYPE_CHECKING, Callable, List, Set, Tuple, TypeVar

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
from bioregistry.bibliometrics import (
    count_publication_years,
    get_oldest_publications,
    get_publications_df,
)
from bioregistry.constants import DOCS_IMG, EXPORT_REGISTRY
from bioregistry.license_standardizer import standardize_license
from bioregistry.schema import Resource
from bioregistry.utils import pydantic_dict

if TYPE_CHECKING:
    import matplotlib.axes
    import matplotlib.figure

logger = logging.getLogger(__name__)

X = TypeVar("X")

# see named colors https://matplotlib.org/stable/gallery/color/named_colors.html
BIOREGISTRY_COLOR = "silver"
BAR_SKIP = {"re3data", "bartoc"}

FigAxPair = tuple["matplotlib.figure.Figure", "matplotlib.axes.Axes"]


class RegistryInfo(typing.NamedTuple):
    """A tuple representing keys."""

    metaprefix: str
    label: str
    color: str
    prefixes: Set[str]


def _get_has(func: Callable[[str], typing.Any], yes: str = "Yes", no: str = "No") -> Counter[str]:
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


def _get_has_present(func: Callable[[str], X | None]) -> Counter[X]:
    values = (func(prefix) for prefix in read_registry())
    return Counter(value for value in values if value)


SINGLE_FIG = (8.25, 3.5)
TODAY = datetime.datetime.today().strftime("%Y-%m-%d")
WATERMARK_TEXT = f"https://github.com/biopragmatics/bioregistry ({TODAY})"


def _save(
    fig: "matplotlib.figure.Figure",
    name: str,
    *,
    svg: bool = True,
    png: bool = False,
    eps: bool = False,
    pdf: bool = False,
) -> None:
    import matplotlib.pyplot as plt

    stub = DOCS_IMG.joinpath(name)
    path = stub.with_suffix(".svg")
    click.echo(f"output to {path}")
    fig.tight_layout()
    if svg:
        fig.savefig(path)
    if eps:
        fig.savefig(stub.with_suffix(".eps"))
    if png:
        fig.savefig(stub.with_suffix(".png"), dpi=300)
    if pdf:
        fig.savefig(stub.with_suffix(".pdf"))
    plt.close(fig)


def plot_attribute_pies(watermark: bool) -> FigAxPair:
    """Plot how many entries have version information."""
    licenses_mapped = _get_licenses_mapped_counter()
    licenses_mapped_counter = Counter(licenses_mapped)
    measurements = [
        ("Name", _get_has(get_name)),
        ("Homepage", _get_has(get_homepage)),
        ("Description", _get_has(get_description)),
        ("Example", _get_has(get_example)),
        ("Pattern", _get_has(get_pattern)),
        ("Provider", _get_has(get_uri_format)),
        ("License", _get_has(get_license)),
        (
            "License Type",
            Counter(
                {
                    license_key: count
                    for license_key, count in licenses_mapped_counter.most_common()
                    if license_key is not None and license_key != "None"
                }
            ),
        ),
        ("Version", _get_has(get_version)),
        ("Contact Email", _get_has(get_contact_email)),
        ("Wikidata Database", HAS_WIKIDATA_DATABASE),
        ("OBO", _get_has(get_obo_download)),
        ("OWL", _get_has(get_owl_download)),
        ("JSON", _get_has(get_json_download)),
    ]
    return _plot_attribute_pies(measurements=measurements, watermark=watermark)


def _plot_attribute_pies(
    *,
    measurements: Collection[Tuple[str, typing.Counter]],
    watermark,
    ncols: int = 4,
    keep_ontology: bool = True,
) -> FigAxPair:
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
    for label_counter, ax in itt.zip_longest(measurements, axes.ravel()):
        if label_counter is None:
            ax.axis("off")
            continue
        label, counter = label_counter
        if label == "License Type":
            labels, sizes = zip(*counter.most_common())
            explode = None
        else:
            labels = ("Yes", "No")
            n_yes = counter.get("Yes", 0)
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


def make_overlaps(keys: List[RegistryInfo]) -> Mapping[str, Mapping[str, Set[str]]]:
    """Make overlaps dictionary."""
    rv = {}
    for metaprefix, _, _, prefixes in keys:
        # Remap bioregistry prefixes to match the external
        #  vocabulary, when possible
        bioregistry_remapped = {
            resource.get_external(metaprefix).get("prefix", prefix)
            for prefix, resource in bioregistry.read_registry().items()
        }
        rv[metaprefix] = {
            REMAPPED_KEY: bioregistry_remapped,
            REMAPPED_VALUE: prefixes,
        }
    return rv


def plot_overlap_venn_diagrams(*, keys, overlaps, watermark, ncols: int = 3):
    """Plot overlap with venn diagrams."""
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


def _plot_external_overlap(*, keys, watermark, ncols: int = 4) -> FigAxPair:
    """Plot the overlap between each pair of resources."""
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


def get_getters() -> list[tuple[str, str, Callable]]:
    """Get getter functions, which requires alignment dependencies."""
    # FIXME replace with class_resolver
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


def get_registry_infos() -> List[RegistryInfo]:
    """Get keys for plots."""
    getters = get_getters()
    try:
        import seaborn as sns
    except ImportError:
        raise
    else:
        palette = sns.color_palette("Paired", len(getters))
    return [
        RegistryInfo(metaprefix, label, color, set(func(force_download=False)))
        for (metaprefix, label, func), color in zip(getters, palette)
    ]


def bibliometric_comparison() -> None:
    """Generate images."""
    import matplotlib.pyplot as plt
    import pandas
    import seaborn as sns

    publications_df = get_publications_df()
    publications_df.to_csv(EXPORT_REGISTRY.joinpath("publications.tsv"), sep="\t", index=False)

    publications = get_oldest_publications()
    year_counter = count_publication_years(publications)
    df = pandas.DataFrame(sorted(year_counter.items()), columns=["year", "count"])

    fig, ax = plt.subplots(figsize=(8, 3.5))
    sns.barplot(data=df, ax=ax, x="year", y="count")
    ax.set_ylabel("Publications")
    ax.set_xlabel("")
    ax.set_title(f"Timeline of First Publications for {len(publications):,} Prefixes")
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(DOCS_IMG.joinpath("bibliography_years.svg"), dpi=350)
    fig.savefig(DOCS_IMG.joinpath("bibliography_years.png"), dpi=350)


@click.command()
def compare() -> None:
    """Compare the registries."""
    paper = False
    random.seed(0)
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        click.secho(
            "Could not import matplotlib dependencies."
            " Install bioregistry again with `pip install bioregistry[charts]`.",
            fg="red",
        )
        raise sys.exit(1)

    bibliometric_comparison()

    registry_infos = get_registry_infos()
    overlaps = make_overlaps(registry_infos)

    # This should make SVG output deterministic
    # See https://matplotlib.org/3.1.0/users/prev_whats_new/whats_new_2.0.0.html#added-svg-hashsalt-key-to-rcparams
    plt.rcParams["svg.hashsalt"] = "saltyregistry"

    watermark = True
    sns.set_style("white")

    fig, _axes = plot_xrefs(registry_infos, watermark=watermark)
    _save(fig, name="xrefs", png=paper, pdf=paper)

    fig, _axes = plot_coverage_gains(overlaps=overlaps)
    _save(fig, name="bioregistry_coverage_bar", png=paper, pdf=paper)

    fig, axes = plot_overlap_venn_diagrams(
        keys=registry_infos, overlaps=overlaps, watermark=watermark
    )
    _save(fig, name="bioregistry_coverage")

    fig, axes = plot_coverage_overlaps(overlaps=overlaps)
    _save(fig, name="bioregistry_coverage_bar_short")

    fig, axes = plot_attribute_pies(watermark=watermark)
    _save(fig, "has_attribute")

    fig, _axes = _plot_external_overlap(keys=registry_infos, watermark=watermark)
    _save(fig, name="external_overlap")

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
    regex_complexities = get_regex_complexities()
    g = sns.displot(x=regex_complexities, log_scale=2, height=3, aspect=4 / 3)
    g.set(
        xlabel="Regular Expression Complexity",
        xlim=(min(regex_complexities), max(regex_complexities)),
    )
    _save(g.figure, name="regex_report", eps=paper)


def _count_providers(resource: Resource) -> int:
    rv = 0
    if resource.get_uri_prefix():
        rv += 1
    rv += len(resource.get_extra_providers())
    return rv


def _get_license_and_conflicts() -> tuple[list[str], set[str], set[str], set[str]]:
    licenses: list[str] = []
    conflicts: set[str] = set()
    obo_has_license: set[str] = set()
    ols_has_license: set[str] = set()
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
            licenses.append(typing.cast(str, ols_license))
        elif obo_license == ols_license:
            licenses.append(typing.cast(str, obo_license))
        else:  # different licenses!
            licenses.append(typing.cast(str, ols_license))
            licenses.append(typing.cast(str, obo_license))
            conflicts.add(key)
            # logger.warning(f"[{key}] Conflicting licenses- {obo_license} and {ols_license}")
            continue
    return licenses, conflicts, obo_has_license, ols_has_license


def _remap(*, key: str, prefixes: Collection[str]) -> Set[str]:
    br_external_to = {}
    for br_id, resource in read_registry().items():
        _k = (pydantic_dict(resource).get(key) or {}).get("prefix")
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
        rows.append(float(len(pattern) - 2))
    return sorted(rows)


def plot_coverage_overlaps(*, overlaps) -> FigAxPair:
    """Plot and save the abridged coverage bar chart."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    sns.set_style("white")

    rows = []
    for metaprefix, data in overlaps.items():
        if metaprefix in BAR_SKIP:
            continue
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

    plt.tight_layout()
    return fig, ax


def plot_coverage_gains(*, overlaps, minimum_width_for_text: int = 70) -> FigAxPair:
    """Plot and save the coverage bar chart."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    sns.set_style("white")

    rows = []
    for metaprefix, data in overlaps.items():
        if metaprefix in BAR_SKIP:
            continue
        # Get the set of remapped bioregistry prefixes
        bioregistry_prefixes = data[REMAPPED_KEY]
        # Get the set of prefixes from the registry with the given metaprefix
        external_prefixes = data[REMAPPED_VALUE]
        rows.append(
            (
                bioregistry.get_registry_short_name(metaprefix),
                # (blue) The number of external prefixes that were not mapped to bioregistry prefixes
                len(external_prefixes - bioregistry_prefixes),
                # (orange) The number of external prefixes that were mapped to bioregistry prefixes
                len(bioregistry_prefixes.intersection(external_prefixes)),
                # (green) The number of bioregistry prefixes that were not mapped to external prefixes
                len(bioregistry_prefixes - external_prefixes),
            )
        )
    rows = sorted(rows, key=lambda row: sum(row[1:]), reverse=True)

    df = pd.DataFrame(rows, columns=["metaprefix", "External Only", "Mapped", "Bioregistry Only"])
    df.set_index("metaprefix", inplace=True)

    fig, ax = plt.subplots(1, 1, figsize=(10, 7.5))
    plt.rc("legend", fontsize=12, loc="upper right")
    fig.subplots_adjust(right=0.4)
    df.plot(
        kind="barh",
        stacked=True,
        ax=ax,
        width=0.85,
        fontsize=14,
        grid=False,
        legend=True,
    )
    plt.legend()
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
    for patch in ax.patches:
        width, height = patch.get_width(), patch.get_height()
        x, y = patch.get_xy()
        dd[y, height].append((width, x))
        if width < minimum_width_for_text:
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

    plt.tight_layout()
    return fig, ax


def plot_xrefs(registry_infos, watermark: bool) -> FigAxPair:
    """Plot a histogram of how many xrefs each entry has."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns

    xref_counts = [
        sum(0 < len(entry.get_external(key)) for key, *_ in registry_infos)
        for entry in read_registry().values()
    ]
    fig, ax = plt.subplots(figsize=SINGLE_FIG)
    xrefs_counter: typing.Counter[int] = Counter(xref_counts)

    mappable_metaprefixes = {
        metaprefix for entry in read_registry().values() for metaprefix in entry.get_mappings()
    }
    n_mappable_metaprefixes = len(mappable_metaprefixes)
    max_mapped = max(xrefs_counter)
    # fill in the missing values
    for i in range(max_mapped):
        if i not in xrefs_counter:
            xrefs_counter[i] = 0
    # add two extra to the right for good measure
    xrefs_counter[max_mapped + 1] = 0
    xrefs_counter[max_mapped + 2] = 0
    # make the last value have a ... as its label rather than a number
    xrefs_rows: List[Tuple[typing.Union[str, int], int]] = sorted(xrefs_counter.items())
    xrefs_rows[-1] = "...", xrefs_rows[-1][1]
    xrefs_df = pd.DataFrame(xrefs_rows, columns=["frequency", "count"])

    palette = sns.color_palette("tab10")
    xrefs_colors = [palette[2]] + ([palette[1]] * (len(xrefs_df.index) - 1))
    sns.barplot(
        data=xrefs_df,
        x="frequency",
        y="count",
        hue="frequency",
        errorbar=None,
        palette=xrefs_colors,
        alpha=1.0,
        ax=ax,
        legend=False,
    )
    # There should only be one container here
    _labels = xrefs_df["count"].to_list()
    _labels[0] = f"{_labels[0]}\nNovel"
    for i, label in zip(ax.containers, _labels):
        ax.bar_label(i, [label])
    ax.set_xlabel(
        f"Number of the {n_mappable_metaprefixes} Mapped External Registries Capturing a Given Identifier Resource"
    )
    ax.set_ylabel("Number of Identifier Resources")
    ax.set_yscale("log")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    x1, _y1 = ax.patches[max_mapped - 1].get_xy()
    x2, _ = ax.patches[-1].get_xy()
    x3, _ = ax.patches[-2].get_xy()
    x_25 = (x2 + x3) / 2.0  # have the arrow point halfway between the last and the ...
    h = 24  # how high should the text go
    ax.text(
        x1,
        h + 1,
        f"No identifier resources are\navailable in more than\n"
        f"{max_mapped} external registries",
        horizontalalignment="center",
        verticalalignment="bottom",
        fontdict=dict(fontsize=12),
    )
    ax.arrow(x1, h, x_25 - x1, 3 - h, head_width=0.3, head_length=0.2, fc="k", ec="k")
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

    #: the distance between the leftmost bar and the y axis line
    offset = 0.7
    ax.set_xlim([-offset, len(ax.patches) - (1 + offset)])
    return fig, ax


def _get_licenses_mapped_counter(threshold: int = 30) -> List[str]:
    licenses, conflicts, obo_has_license, ols_has_license = _get_license_and_conflicts()
    licenses_counter: typing.Counter[str] = Counter(licenses)
    licenses_mapped = [
        (
            "None"
            if license_ is None
            else license_ if licenses_counter[license_] > threshold else "Other"
        )
        for license_ in licenses
    ]
    return licenses_mapped


if __name__ == "__main__":
    compare()
