"""A benchmark for Bioregistry's CURIE validator."""

import random
import time
from collections.abc import Iterable
from typing import cast

import click
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from tqdm import tqdm, trange
from typing_extensions import TypeAlias

import bioregistry
from bioregistry import manager
from bioregistry.constants import CURIE_VALIDATION_DATA_PATH, CURIE_VALIDATION_SVG_PATH
from bioregistry.utils import curie_to_str

Row: TypeAlias = tuple[str, str, str, str]


def get_curies(rebuild: bool = True) -> list[Row]:
    """Get prefix-identifier-banana-curie tuples for benchmarking."""
    if CURIE_VALIDATION_DATA_PATH.is_file() and not rebuild:
        return [
            cast(Row, line.strip().split("\t"))
            for line in CURIE_VALIDATION_DATA_PATH.read_text().splitlines()
        ]
    rows = sorted(set(iter_curies()))
    CURIE_VALIDATION_DATA_PATH.write_text("\n".join("\t".join(line) for line in rows))
    return rows


def iter_curies() -> Iterable[Row]:
    """Generate prefix-identifier-banana-curie tuples for benchmarking."""
    for prefix, resource in tqdm(
        manager.registry.items(), desc="Generating test CURIEs", unit="prefix"
    ):
        pattern = resource.get_pattern()
        if not pattern:
            continue
        synonyms = resource.get_synonyms()
        for example in resource.get_examples():
            yield prefix, example, "true", curie_to_str(prefix, example)
            for synonym in synonyms:
                yield prefix, example, "false", curie_to_str(synonym, example)
            for mutilation in [
                f"{example}!",
                f"!{example}",
            ]:
                yield prefix, mutilation, "false", curie_to_str(prefix, mutilation)
        for counterexample in resource.example_decoys or []:
            yield prefix, counterexample, "false", curie_to_str(prefix, counterexample)
            for synonym in synonyms:
                yield prefix, counterexample, "false", curie_to_str(synonym, counterexample)
        banana = resource.get_banana()
        if banana:
            peel = resource.get_banana_peel()
            for example in resource.get_examples():
                example_extended = f"{banana}{peel}{example}"
                yield prefix, example_extended, "false", curie_to_str(prefix, example_extended)
                for synonym in synonyms:
                    yield prefix, example_extended, "false", curie_to_str(synonym, example_extended)


@click.command()
@click.option("--rebuild", is_flag=True)
@click.option("--replicates", type=int, default=10)
def main(rebuild: bool, replicates: int) -> None:
    """Test validating CURIEs."""
    curies = get_curies(rebuild=rebuild)

    # warm up cache
    bioregistry.is_valid_curie("DRON:00023232")

    rows_ = []
    failures = 0
    xx = set()
    for _ in trange(replicates, desc="Test validating CURIEs", unit="replicate"):
        random.shuffle(curies)
        for prefix, identifier, label, curie in tqdm(
            curies, unit_scale=True, unit="CURIE", leave=False
        ):
            start = time.time()
            result = bioregistry.is_valid_curie(curie)
            rows_.append((time.time() - start, label))
            if result is None:
                tqdm.write(f"Missing pattern for {curie}")
            elif result is True and label == "false":
                failures += 1
                if (prefix, identifier, label, curie) not in xx:
                    xx.add((prefix, identifier, label, curie))
                    tqdm.write(
                        f"expecting {curie} to be invalid against (got {result} but expected false)"
                    )
            elif result is False and label == "true":
                failures += 1
                if (prefix, identifier, label, curie) not in xx:
                    xx.add((prefix, identifier, label, curie))
                    tqdm.write(f"expecting {curie} to be valid (got {result} but expected true)")

    df = pd.DataFrame(rows_, columns=["time", "label"])
    m = df["time"].mean()
    title = (
        f"Bioregistry CURIE Validation Benchmark\nAverage: {round(1 / m):,} CURIE/s, "
        f"Errors: {failures // replicates}"
    )
    click.echo(title)

    fig, ax = plt.subplots()
    sns.histplot(data=df[df["time"] > 0], x="time", hue="label", ax=ax, log_scale=True)
    ax.axvline(m)
    ax.set_xlabel("Time (seconds)")
    ax.set_title(title)
    fig.savefig(CURIE_VALIDATION_SVG_PATH)


if __name__ == "__main__":
    main()
