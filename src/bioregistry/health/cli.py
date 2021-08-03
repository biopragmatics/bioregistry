# -*- coding: utf-8 -*-

"""A central CLI for Bioregistry health checks."""

import click

from . import check_homepages, check_providers

__all__ = [
    "main",
]

# TODO add default command that runs them all

main = click.Group(
    name="health",
    commands={
        "homepages": check_homepages.main,
        "providers": check_providers.main,
    },
)

if __name__ == "__main__":
    main()
