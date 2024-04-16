# -*- coding: utf-8 -*-

"""Run all benchmarks."""

import click

from . import curie_parsing, curie_validation, uri_parsing


@click.command()
@click.option("--rebuild", is_flag=True)
@click.option("--replicates", type=int, default=10)
@click.pass_context
def main(ctx: click.Context, rebuild: bool, replicates: int):
    """Run all benchmarks."""
    ctx.invoke(curie_parsing.main, rebuild=rebuild, replicates=replicates)
    ctx.invoke(uri_parsing.main, rebuild=rebuild, replicates=replicates)
    ctx.invoke(curie_validation.main, rebuild=rebuild, replicates=replicates)


if __name__ == "__main__":
    main()
