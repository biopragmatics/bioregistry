"""Add WorldAvatar ontologies."""

import click
import obographs
import pystow
import robot_obo_tool
from pystow.github import get_contents
from pystow.utils import safe_open_json, write_json
from tqdm import tqdm

from bioregistry import Author, Manager, Resource


@click.command()
@click.option("--force-process", is_flag=True)
def main(force_process: bool) -> None:
    """Add WorldAvatar ontologies."""
    manager = Manager()

    module = pystow.module("worldavatar")

    outer_contents_cache = module.join(name="ontologies.json")
    if outer_contents_cache.exists():
        outer_records = safe_open_json(outer_contents_cache)
    else:
        outer_records = get_contents("TheWorldAvatar", "ontology", "ontology")
        write_json(outer_records, outer_contents_cache, indent=2)

    for outer_record in tqdm(outer_records, desc="Preparing WorldAvatar ontologies"):
        worldavatar_name = outer_record["name"]
        if not worldavatar_name.startswith("onto"):
            continue
        short = worldavatar_name.removeprefix("onto")
        prefix = "worldavatar." + short
        if prefix in manager.registry and not force_process:
            tqdm.write(f"[{prefix}] already registered")
            continue

        github_relative_filepath = outer_record["path"]
        inner_contents_cache = module.join(name=f"{short}.json")
        if inner_contents_cache.is_file():
            inner_records = safe_open_json(inner_contents_cache)
        else:
            inner_records = get_contents("TheWorldAvatar", "ontology", github_relative_filepath)
            tqdm.write(f"[{prefix}] caching GitHub results to {inner_contents_cache}")
            write_json(inner_records, inner_contents_cache, indent=2)

        try:
            inner_record = next(
                inner_record
                for inner_record in inner_records
                if inner_record["name"].endswith(".owl") or inner_record["name"].endswith(".ttl")
            )
        except StopIteration:
            tqdm.write(
                click.style(
                    f"[{prefix}] no owl file found - see https://github.com/TheWorldAvatar/ontology/blob/main/{github_relative_filepath}",
                    fg="yellow",
                )
            )
            continue
        name = "WorldAvatar " + inner_record["name"].removesuffix(".owl")

        download_owl = inner_record["download_url"]
        owl_path = module.ensure(url=download_owl)
        obograph_json_path = owl_path.with_suffix(".obograph.json")
        if not obograph_json_path.is_file():
            try:
                robot_obo_tool.convert(owl_path, obograph_json_path)
            except Exception:
                tqdm.write(
                    click.style(
                        f"[{prefix}] exception when converting to obograph json", fg="yellow"
                    )
                )
                continue

        uri_format: str | None = None
        example: str | None = None
        description: str | None = None
        try:
            obograph = obographs.read(obograph_json_path, squeeze=True)
        except Exception:
            tqdm.write(click.style(f"[{prefix}] exception when reading obograph json", fg="yellow"))
        else:
            if not obograph.nodes:
                click.style(f"[{prefix}] has no nodes, so couldn't guess URI format", fg="yellow")
            else:
                if obograph.id is not None:
                    uri_format, example = _guess(obograph, obograph.id + "#")
                for guess in [
                    f"https://www.theworldavatar.com/kg/{worldavatar_name}/",
                    f"http://www.theworldavatar.com/kg/{worldavatar_name}/",
                    f"https://www.theworldavatar.io/kg/{worldavatar_name}/",
                    f"http://www.theworldavatar.io/kg/{worldavatar_name}/",
                ]:
                    if uri_format is None:
                        uri_format, example = _guess(obograph, guess)
                if uri_format is None:
                    tqdm.write(
                        click.style(
                            f"[{prefix}] couldn't guess URI format ({worldavatar_name}), look manually",
                            fg="yellow",
                        )
                    )

            # try to guess a description
            if obograph.meta and obograph.meta:
                description = obograph._get_property(
                    "http://purl.org/dc/terms/description"
                ) or obograph._get_property("http://www.w3.org/2000/01/rdf-schema#comment")
            if description is None:
                tqdm.write(click.style(f"[{prefix}] no description", fg="yellow"))

        resource = Resource(
            prefix=prefix,
            name=name,
            description=description,
            uri_format=uri_format,
            example=example,
            homepage="https://theworldavatar.io",
            part_of_database="worldavatar",
            repository="https://github.com/TheWorldAvatar/ontology",
            contributor=Author.get_charlie(),
            download_owl=download_owl,
            contact_group_email="contact@theworldavatar.io",
            contact=Author(
                name="Hou Yee Quek",
                orcid="0000-0002-3168-237X",
                github="qhouyee",
            ),
        )
        manager.add_resource(resource)

    manager.write_registry()


def _guess(obograph: obographs.Graph, guess_uri_prefix: str) -> tuple[str, str] | tuple[None, None]:
    for node in obograph.nodes:
        if node.id.startswith(guess_uri_prefix):
            uri_format = guess_uri_prefix + "$1"
            example = node.id.removeprefix(guess_uri_prefix)
            return uri_format, example
    return None, None


if __name__ == "__main__":
    main()
