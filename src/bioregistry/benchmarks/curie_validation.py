"""A benchmark for Bioregistry's CURIE validator."""

import itertools as itt
import random
import time
from statistics import mean
from typing import Iterable, Tuple
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm, trange

import bioregistry
from bioregistry import manager
from bioregistry.constants import (
    CURIE_VALIDATION,
    CURIE_VALIDATION_DATA_PATH,
    CURIE_VALIDATION_SVG_PATH,
)
from bioregistry.utils import curie_to_str


def get_curies(rebuild: bool = True):
    """Get prefix-identifier-banana-curie tuples for benchmarking."""
    if CURIE_VALIDATION_DATA_PATH.is_file() and not rebuild:
        return [
            line.strip().split("\t") for line in CURIE_VALIDATION_DATA_PATH.read_text().splitlines()
        ]
    rows = sorted(set(iter_curies()))
    CURIE_VALIDATION_DATA_PATH.write_text("\n".join("\t".join(line) for line in rows))
    return rows


def iter_curies() -> Iterable[Tuple[str, str, str, str, str]]:
    """Generate prefix-identifier-banana-curie tuples for benchmarking."""
    for prefix, resource in tqdm(
        manager.registry.items(), desc="Generating test CURIEs", unit="prefix"
    ):
        for example in resource.get_examples():
            yield prefix, example, "true", curie_to_str(prefix, example)
        for counterexample in resource.example_decoys or []:
            yield prefix, counterexample, "false", curie_to_str(prefix, counterexample)
        for synonym in resource.get_synonyms():
            yield prefix, example, "false", curie_to_str(synonym, example)
        banana = resource.get_banana()
        if banana:
            peel = resource.get_banana_peel()
            example_extended = f"{banana}{peel}{example}"
            yield prefix, example_extended, "false", curie_to_str(prefix, example_extended)
        # TODO generate more false examples from identifier mutilation


def main(rebuild: bool = True, epochs: int = 10):
    """Test validating CURIEs."""
    curies = get_curies(rebuild=rebuild)

    # warm up cache
    bioregistry.is_valid_curie("DRON:00023232")

    rows_ = []
    failures = 0
    xx = set()
    for _ in trange(epochs, desc="epochs"):
        random.shuffle(curies)
        for prefix, identifier, label, curie in tqdm(curies, unit_scale=True, unit="CURIE", leave=False):
            start = time.time()
            result = bioregistry.is_valid_curie(curie)
            rows_.append((time.time() - start, label))
            if result and label != "true":
                failures += 1
                if (prefix, identifier, label, curie) not in xx:
                    xx.add((prefix, identifier, label, curie))
                    tqdm.write(f"incorrect validation {curie} (expected {label})")

    fig, ax = plt.subplots()
    df = pd.DataFrame(rows_, columns=["time", "label"])
    sns.histplot(data=df, x="time", hue="label", ax=ax, log_scale=True)
    m = df["time"].mean()
    ax.axvline(m)
    ax.set_xlabel("Time (seconds)")
    ax.set_title(
        f"Bioregistry CURIE Validation Benchmark\nAverage: {round(1 / m):,} CURIE/s, Errors: {failures // epochs}"
    )
    fig.savefig(CURIE_VALIDATION_SVG_PATH)


if __name__ == "__main__":
    main()
