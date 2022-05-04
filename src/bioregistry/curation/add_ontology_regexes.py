# -*- coding: utf-8 -*-

"""Assert regular expression patterns for common identifier styles."""

import re

import click
import tabulate

import bioregistry


def _examples(resource):
    rv = []
    example = resource.get_example()
    if example:
        rv.append(example)
    rv.extend(resource.example_extras or [])
    return rv


@click.command()
def _main():
    registry = bioregistry.read_registry()
    rows = []
    for prefix, resource in registry.items():
        pattern = resource.get_pattern()
        if pattern:
            continue
        examples = _examples(resource)
        if not examples:
            continue
        example = examples[0]

        if len(example) > 10:
            continue  # skip long examples
        if example.startswith("0"):
            pattern = f"^\\d{{{len(example)}}}$"
            if not all(re.match(pattern, e) for e in examples):
                click.echo(f"Check prefix: {prefix}")
                continue
            resource.pattern = pattern
            rows.append((prefix, example, resource.pattern))
        elif example.isnumeric():
            pattern = "^\\d+$"
            if not all(re.match(pattern, e) for e in examples):
                click.echo(f"Check prefix: {prefix}")
                continue
            resource.pattern = pattern
            rows.append((prefix, example, resource.pattern))
        else:
            rows.append((prefix, example, "???"))

    click.echo(tabulate.tabulate(rows, headers=["prefix", "example", "pattern"]))
    bioregistry.write_registry(registry)


if __name__ == "__main__":
    _main()
