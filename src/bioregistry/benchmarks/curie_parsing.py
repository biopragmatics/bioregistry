"""A benchmark for Bioregistry's CURIE parser."""

import time
from typing import Iterable, Tuple

import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

import bioregistry
from bioregistry import manager
from bioregistry.constants import CURIE_PARSING_DATA_PATH, CURIE_PARSING_SVG_PATH
import itertools as itt


def get_curies(rebuild: bool = True):
    """Get prefix-identifier-banana-curie tuples for benchmarking."""
    if CURIE_PARSING_DATA_PATH.is_file() and not rebuild:
        return [line.strip().split("\t") for line in CURIE_PARSING_DATA_PATH.read_text().splitlines()]
    rows = sorted(set(iter_curies()))
    CURIE_PARSING_DATA_PATH.write_text("\n".join("\t".join(line) for line in rows))
    return rows


def iter_curies() -> Iterable[Tuple[str, str, str, str]]:
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


def main(rebuild: bool = False):
    """Test parsing CURIEs."""
    curies = get_curies(rebuild=rebuild)

    # warm up cache
    bioregistry.parse_curie("DRON:00023232")

    times = []
    for prefix, synonym, identifier, banana, curie in tqdm(curies, unit_scale=True, unit="URI"):
        start = time.time()
        p, i = bioregistry.parse_curie(curie)
        times.append(time.time() - start)
        if p != prefix or i != identifier:
            tqdm.write(f"failed on {curie} to get {prefix}:{identifier}")

    fig, ax = plt.subplots()
    sns.histplot(data=times, ax=ax, log_scale=True)
    ax.set_xlabel("Time (seconds)")
    ax.set_title("Bioregistry CURIE Parsing Benchmark")
    fig.savefig(CURIE_PARSING_SVG_PATH)


if __name__ == "__main__":
    main()
