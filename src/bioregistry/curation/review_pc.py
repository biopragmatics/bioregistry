"""Help review prefix commons imports."""

import webbrowser

import click
import pandas

from bioregistry import Author, manager
from bioregistry.constants import BIOREGISTRY_MODULE


@click.command()
def main() -> None:
    """Run the prefix commons import reviewer workflow."""
    reviewed_count = 0
    rows = []
    for prefix, resource in sorted(manager.registry.items()):
        if set(resource.get_mappings()) != {"prefixcommons"}:
            continue
        if resource.contributor:
            continue
        if resource.reviewer:
            reviewed_count += 1
            rows.append(
                (prefix, resource.is_deprecated(), resource.provides, resource.get_example_iri())
            )
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
            reviewed_count += 1
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
            reviewed_count += 1
        else:
            continue

    click.echo(f"{reviewed_count} were reviewed")
    df = pandas.DataFrame(rows, columns=["prefix", "deprecated", "provides", "example_url"])
    path = BIOREGISTRY_MODULE.join(name="pc_results.tsv")
    df.to_csv(path, sep="\t", index=False)
    click.echo(f"Output results to {path}")


if __name__ == "__main__":
    main()
