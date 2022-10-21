"""Help review prefix commons imports."""

import webbrowser

import click

from bioregistry import Author, manager


@click.command()
def main():
    """Run the prefix commons import reviewer workflow."""
    for prefix, resource in sorted(manager.registry.items()):
        if set(resource.get_mappings()) != {"prefixcommons"}:
            continue
        if resource.reviewer or resource.contributor:
            continue
        homepage = resource.get_homepage()
        example_iri = resource.get_example_iri()
        if example_iri is None or homepage is None:
            continue
        webbrowser.open_new_tab(example_iri)
        res = input(f"[{prefix}] type y or yes to accept, anything else to continue: ")
        if res.lower() in {"yes", "y"}:
            resource.reviewer = Author(
                name="Charles Tapley Hoyt",
                orcid="0000-0003-4423-4370",
                email="cthoyt@gmail.com",
                github="cthoyt",
            )
            manager.write_registry()
        elif res.lower() in {"n", "no"}:
            resource.deprecated = True
            resource.comment = "This resource doesn't exist on the web anymore"
            resource.reviewer = Author(
                name="Charles Tapley Hoyt",
                orcid="0000-0003-4423-4370",
                email="cthoyt@gmail.com",
                github="cthoyt",
            )
            manager.write_registry()
        else:
            continue


if __name__ == "__main__":
    main()
