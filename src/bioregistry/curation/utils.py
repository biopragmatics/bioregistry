"""Utilities for curation scripts."""

from collections.abc import Callable

import click

from bioregistry import Resource, manager, Manager

__all__ = [
    "resource_mutator",
    "manager_mutator",
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
            for resource in manager.registry.values():
                func(resource)
            manager.write_registry()

        return _main

    return _inner
