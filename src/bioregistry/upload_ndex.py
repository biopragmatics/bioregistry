# -*- coding: utf-8 -*-

"""Generate a small knowledge graph relating entities."""

import click
import pystow
from more_click import verbose_option
from ndex2 import NiceCXBuilder

import bioregistry
import bioregistry.version

NDEX_UUID = "aa78a43f-9c4d-11eb-9e72-0ac135e8bacf"


@click.command()
@verbose_option
def main():
    """Upload the Bioregistry KG to NDEx."""
    upload()
    click.echo(f"see https://bioregistry.io/ndex:{NDEX_UUID}")


def upload():
    """Generate a CX graph and upload to NDEx."""
    cx = NiceCXBuilder()
    cx.set_name("Bioregistry")
    cx.add_network_attribute(
        "description",
        "An integrative meta-registry of biological databases, ontologies, and nomenclatures",
    )
    cx.add_network_attribute("hash", bioregistry.version.get_git_hash())
    cx.add_network_attribute("version", bioregistry.version.get_version())
    cx.set_context(
        {
            "bioregistry.collection": "https://bioregistry.io/collection/",
            "bioregistry.registry": "https://bioregistry.io/metaregistry/",
            "bioregistry": "https://bioregistry.io/registry/",
        }
    )

    metaregistry = bioregistry.read_metaregistry()
    registry = bioregistry.read_registry()

    registry_nodes = {metaprefix: make_registry_node(cx, metaprefix) for metaprefix in metaregistry}
    resource_nodes = {prefix: make_resource_node(cx, prefix) for prefix in registry}

    for prefix, entry in registry.items():
        # Who does it provide for?
        provides = bioregistry.get_provides_for(prefix)
        if isinstance(provides, str):
            provides = [provides]
        for target in provides or []:
            cx.add_edge(
                source=resource_nodes[prefix],
                target=resource_nodes[target],
                interaction="provides",
            )
        if entry.part_of and entry.part_of in resource_nodes:
            cx.add_edge(
                source=resource_nodes[prefix],
                target=resource_nodes[entry.part_of],
                interaction="part_of",
            )
        if entry.has_canonical:
            cx.add_edge(
                source=resource_nodes[prefix],
                target=resource_nodes[entry.has_canonical],
                interaction="has_canonical",
            )

        # Which registries does it map to?
        for metaprefix in metaregistry:
            if metaprefix not in entry:
                continue
            cx.add_edge(
                source=resource_nodes[prefix],
                target=registry_nodes[metaprefix],
                interaction="listed",
            )

    for collection_id, collection in bioregistry.read_collections().items():
        source = cx.add_node(
            name=collection.name,
            represents=f"bioregistry.collection:{collection_id}",
        )
        if collection.description:
            cx.add_node_attribute(source, "description", collection.description)
        for prefix in collection.resources:
            cx.add_edge(
                source=source,
                target=resource_nodes[prefix],
                interaction="has_prefix",
            )

    nice_cx = cx.get_nice_cx()
    nice_cx.update_to(
        uuid=NDEX_UUID,
        server="http://public.ndexbio.org",
        username=pystow.get_config("ndex", "username"),
        password=pystow.get_config("ndex", "password"),
    )


def make_registry_node(cx: NiceCXBuilder, metaprefix: str) -> int:
    """Generate a CX node for a registry."""
    node = cx.add_node(
        name=bioregistry.get_registry_name(metaprefix),
        represents=f"bioregistry.registry:{metaprefix}",
    )
    homepage = bioregistry.get_registry_homepage(metaprefix)
    if homepage:
        cx.add_node_attribute(node, "homepage", homepage)
    description = bioregistry.get_registry_description(metaprefix)
    if description:
        cx.add_node_attribute(node, "description", description)
    return node


def make_resource_node(cx: NiceCXBuilder, prefix: str) -> int:
    """Generate a CX node for a resource."""
    node = cx.add_node(
        name=bioregistry.get_name(prefix),
        represents=f"bioregistry:{prefix}",
    )
    homepage = bioregistry.get_homepage(prefix)
    if homepage:
        cx.add_node_attribute(node, "homepage", homepage)
    description = bioregistry.get_description(prefix)
    if description:
        cx.add_node_attribute(node, "description", description)
    pattern = bioregistry.get_pattern(prefix)
    if pattern:
        cx.add_node_attribute(node, "pattern", pattern)
    # TODO add more
    return node


if __name__ == "__main__":
    main()
