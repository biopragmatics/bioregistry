"""Utilities for curation scripts."""

from collections.abc import Callable

import click
from tqdm import tqdm

from bioregistry import Manager, Resource

__all__ = [
    "manager_mutator",
    "resource_mutator",
]

ResourceConsumer = Callable[[Resource], None]
ManagerConsumer = Callable[[Manager], None]


def manager_mutator(*, name: str | None = None) -> Callable[[ManagerConsumer], click.Command]:
    """Decorate a manager-mutating function.

    :param name: The name for the CLI
    :returns: A function decorator
    """

    def _inner(func: ManagerConsumer) -> click.Command:
        @click.command(name=name)
        def _main() -> None:
            manager = Manager()
            func(manager)
            manager.write_registry()

        return _main

    return _inner


def resource_mutator(*, name: str | None = None) -> Callable[[ResourceConsumer], click.Command]:
    """Decorate a resource-mutating function.

    :param name: The name for the CLI
    :returns: A function decorator
    """

    def _inner(func: ResourceConsumer) -> click.Command:
        @click.command(name=name)
        def _main() -> None:
            manager = Manager()
            for resource in tqdm(
                manager.registry.values(), unit="resource", unit_scale=True, leave=False
            ):
                func(resource)
            manager.write_registry()

        return _main

    return _inner
