"""A benchmark for Bioregistry's CURIE parser."""

import itertools as itt
import random
import time
from statistics import mean
from typing import Iterable, Tuple

import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

import bioregistry
from bioregistry import manager
from bioregistry.constants import CURIE_PARSING_DATA_PATH, CURIE_PARSING_SVG_PATH


def get_curies(rebuild: bool = True):
    """Get prefix-identifier-banana-curie tuples for benchmarking."""
    if CURIE_PARSING_DATA_PATH.is_file() and not rebuild:
        return [
            line.strip().split("\t") for line in CURIE_PARSING_DATA_PATH.read_text().splitlines()
        ]
    rows = sorted(set(iter_curies()))
    CURIE_PARSING_DATA_PATH.write_text("\n".join("\t".join(line) for line in rows))
    return rows


def iter_curies() -> Iterable[Tuple[str, str, str, str, str]]:
    """Generate prefix-identifier-banana-curie tuples for benchmarking."""
    for prefix, resource in tqdm(
        manager.registry.items(), desc="Generating test CURIEs", unit="prefix"
    ):
        examples = resource.get_examples()
        prefixes = [prefix]
        preferred_prefix = resource.get_preferred_prefix()
        if preferred_prefix:
            prefixes.append(preferred_prefix)
        for synonym in resource.get_synonyms():
            if " " in synonym:
                continue
            if ":" in synonym:
                continue
            prefixes.append(synonym)
        for p, e in itt.product(prefixes, examples):
            yield prefix, e, p, "", f"{p}:{e}"

        banana = resource.get_banana()
        if banana is not None:
            peel = resource.get_banana_peel()
            banana_extended = f"{banana}{peel}"
            for p, e in itt.product(prefixes, examples):
                example_extended = f"{banana_extended}{e}"
                yield prefix, e, p, banana_extended, f"{p}:{example_extended}"


def main(rebuild: bool = False, epochs: int = 10):
    """Test parsing CURIEs."""
    curies = get_curies(rebuild=rebuild)

    # warm up cache
    bioregistry.parse_curie("DRON:00023232")

    times = []
    failures = 0
    for _ in range(epochs):
        random.shuffle(curies)
        for prefix, identifier, _synonym, _banana, curie in tqdm(
            curies, unit_scale=True, unit="CURIE"
        ):
            start = time.time()
            p, i = bioregistry.parse_curie(curie)
            times.append(time.time() - start)
            if p != prefix or i != identifier:
                failures += 1
                tqdm.write(f"failed on {curie} to get {prefix}:{identifier}")

    fig, ax = plt.subplots()
    sns.histplot(data=times, ax=ax, log_scale=True)
    m = mean(times)
    ax.axvline(m)
    ax.set_xlabel("Time (seconds)")
    ax.set_title(
        f"Bioregistry CURIE Parsing Benchmark\nAverage: {round(1/m):,} CURIE/s, Errors: {failures // epochs}"
    )
    fig.savefig(CURIE_PARSING_SVG_PATH)


if __name__ == "__main__":
    main()
