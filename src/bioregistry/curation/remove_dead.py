"""
Go through each source and remove mappings that are to
resources that don't exist
"""

import json

from bioregistry.external.align import aligner_resolver
import click

from bioregistry.constants import BIOREGISTRY_PATH


@click.command()
def main() -> None:
    """Remove mappings that have been manually curated as false."""
    registry = json.loads(BIOREGISTRY_PATH.read_text())

    for aligner_cls in aligner_resolver:
        if aligner_cls.key == "fairsharing":
            continue  # needs to update fairsharing to bring along deprecated records
        click.echo(aligner_cls.key)
        data = aligner_cls.getter(force_download=False)
        for record in registry.values():
            mappings = record.get("mappings")
            if not mappings:
                continue
            value = mappings.get(aligner_cls.key)
            if not value:
                continue
            if value not in data:
                del record["mappings"][aligner_cls.key]
                del record[aligner_cls.key]

    for v in registry.values():
        if "mappings" in v and not v["mappings"]:
            del v["mappings"]

    BIOREGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
