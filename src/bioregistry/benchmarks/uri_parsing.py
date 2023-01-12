"""A benchmark for Bioregistry's URI parser."""

import time
from statistics import mean
from typing import Iterable, Tuple

import click
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm, trange

import bioregistry
from bioregistry import manager
from bioregistry.constants import URI_PARSING_DATA_PATH, URI_PARSING_SVG_PATH


def get_uris(rebuild: bool = True):
    """Get prefix-identifier-metaprefix-url quads for benchmarking."""
    if URI_PARSING_DATA_PATH.is_file() and not rebuild:
        return [line.strip().split("\t") for line in URI_PARSING_DATA_PATH.read_text().splitlines()]
    uris = sorted(set(iter_uris()))
    URI_PARSING_DATA_PATH.write_text("\n".join("\t".join(line) for line in uris))
    return uris


def iter_uris() -> Iterable[Tuple[str, str, str, str]]:
    """Generate prefix-identifier-metaprefix-url quads for benchmarking."""
    for prefix, resource in tqdm(
        manager.registry.items(), desc="Generating test URIs", unit="prefix"
    ):
        example = resource.get_example()
        if not example:
            continue
        for metaprefix, url in manager.get_providers_list(prefix, example):
            if url.endswith(example):  # skip funny formats
                yield prefix, example, metaprefix, url
        for extra_example in resource.example_extras or []:
            for metaprefix, url in manager.get_providers_list(prefix, extra_example):
                if url.endswith(extra_example):
                    yield prefix, extra_example, metaprefix, url


@click.command()
@click.option("--rebuild", is_flag=True)
@click.option("--replicates", type=int, default=10)
def main(rebuild: bool, replicates: int):
    """Test parsing IRIs."""
    uris = get_uris(rebuild=rebuild)

    # warm up cache
    bioregistry.parse_iri("https://bioregistry.io/DRON:00023232")

    times = []
    for _ in trange(replicates, desc="Test parsing URIs", unit="replicate"):
        for _, _, _, url in tqdm(uris, unit_scale=True, unit="URI"):
            start = time.time()
            bioregistry.parse_iri(url)
            times.append(time.time() - start)

    mean_time = mean(times)
    title = f"Bioregistry URI Parsing Benchmark\nAverage: {round(1 / mean_time):,} URI/s"
    click.echo(title)

    fig, ax = plt.subplots()
    sns.histplot(data=times, ax=ax, log_scale=True)
    ax.set_xlabel("Time (seconds)")
    ax.set_title(title)
    fig.savefig(URI_PARSING_SVG_PATH)


if __name__ == "__main__":
    main()
