# -*- coding: utf-8 -*-

"""Generate a small knowledge graph relating entities."""

import click
import pystow
from more_click import verbose_option
from ndex2 import NiceCXBuilder

import bioregistry
import bioregistry.resolve

NDEX_UUID = "aa78a43f-9c4d-11eb-9e72-0ac135e8bacf"


@click.command()
@verbose_option
def main():
    """Upload the Bioregistry KG to NDEx."""
    upload()


def upload():
    """Generate a CX graph and upload to NDEx."""
    cx = NiceCXBuilder()
    cx.set_name("Bioregistry")
    cx.add_network_attribute(
        "description",
        "An integrative meta-registry of biological databases, ontologies, and nomenclatures",
    )
    cx.add_network_attribute("author", "Charles Tapley Hoyt")
    cx.set_context(
        {
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
        provides = bioregistry.resolve.get_provides_for(prefix)
        if isinstance(provides, str):
            provides = [provides]
        for target in provides or []:
            cx.add_edge(
                source=resource_nodes[prefix],
                target=resource_nodes[target],
                interaction="provides",
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
        represents=f"bioregistry.resource:{prefix}",
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
