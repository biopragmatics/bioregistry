"""Remove uninformative suffixes in names of resources.

For example, renames ``IEEE Xplore document ID`` to ``IEEE Xplore document``.
"""

from tqdm import tqdm

from bioregistry import Resource
from bioregistry.curation.utils import resource_mutator

SUFFIXES = ["id", "accession"]


@resource_mutator()
def clean_name_suffixes(resource: Resource) -> None:
    """Remove uninformative suffixes in names of resources."""
    name = resource.get_name()
    if not name:
        return
    for suffix in SUFFIXES:
        if name.lower().endswith(f" {suffix}"):
            resource.name = name[: -len(suffix) - 1]
            tqdm.write(f"[{resource.prefix}] removing suffix {suffix} from {name}")


if __name__ == "__main__":
    clean_name_suffixes()
