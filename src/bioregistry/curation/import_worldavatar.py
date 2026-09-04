"""Add WorldAvatar ontologies."""

import pystow
from pystow.github import get_contents
import click
from pystow.utils import safe_open_json, write_json
from bioregistry import Manager, Resource, Author
from tqdm import tqdm


@click.command()
def main() -> None:
    """Add WorldAvatar ontologies."""
    manager = Manager()

    outer_contents_cache = pystow.join("worldavatar", name="ontologies.json")
    if outer_contents_cache.exists():
        outer_contents = safe_open_json(outer_contents_cache)
    else:
        outer_contents = get_contents("TheWorldAvatar", "ontology", "ontology")
        write_json(outer_contents, outer_contents_cache)

    for outer_contents in tqdm(outer_contents[:5], desc='Preparing WorldAvatar ontologies'):
        worldavatar_name = outer_contents['name']
        tqdm.write(worldavatar_name)
        if not worldavatar_name.startswith("onto"):
            continue

        short = worldavatar_name.removeprefix("onto")
        prefix = "worldavatar." + short
        if prefix in manager.registry:
            tqdm.write(f"[{prefix}] already registered")
            continue

        path = outer_contents['path']

        inner_contents_cache = pystow.join("worldavatar", name=f"{short}.json")
        if inner_contents_cache.is_file():
            inner_contents = safe_open_json(inner_contents_cache)
        else:
            inner_contents = get_contents("TheWorldAvatar", "ontology", path)
            tqdm.write(f"[{prefix}] caching GitHub results to {inner_contents_cache}")
            write_json(inner_contents, inner_contents_cache)

        inner_contents = next(
            inner_contents
            for inner_contents in inner_contents
            if inner_contents['name'].endswith(".owl")
        )
        name = "WorldAvatar " + inner_contents['name'].removesuffix(".owl")
        resource = Resource(
            prefix=prefix,
            name=name,
            description="",
            uri_format="",
            homepage="https://theworldavatar.io",
            part_of_database="worldavatar",
            repository="https://github.com/TheWorldAvatar/ontology",
            contributor=Author.get_charlie(),
        )
        manager.add_resource(resource)

    manager.write_registry()


if __name__ == '__main__':
    main()
