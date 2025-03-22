"""A central CLI for Bioregistry health checks."""

import click
from click_default_group import DefaultGroup

from . import check_homepages, check_providers

__all__ = [
    "main",
]

COMMANDS = {
    "homepages": check_homepages.main,
    "providers": check_providers.main,
}


@click.group(
    name="health",
    commands=COMMANDS.copy(),
    cls=DefaultGroup,
    default="all",
    default_if_no_args=True,
)
def main() -> None:
    """Run the bioregistry health tests."""


@main.command(name="all")
@click.pass_context
def run_all_commands(ctx: click.Context) -> None:
    """Run all."""
    for name, command in COMMANDS.items():
        click.secho(f"Running python -m bioregistry.health {name}", fg="green")
        ctx.invoke(command)


if __name__ == "__main__":
    main()
