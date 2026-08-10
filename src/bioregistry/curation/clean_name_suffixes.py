"""Remove uninformative suffixes in names of resources.

For example, renames ``IEEE Xplore document ID`` to ``IEEE Xplore document``.
"""

from bioregistry.curation.utils import resource_mutator
from tqdm import tqdm

SUFFIXES = ["id", "accession"]


@resource_mutator()
def remove_uninformative_suffix(resource) -> None:
    name = resource.get_name()
    if not name:
        return
    for suffix in SUFFIXES:
        if name.lower().endswith(f" {suffix}"):
            resource.name = name[: -len(suffix) - 1]
            tqdm.write(f"[{resource.prefix}] removing suffix {suffix} from {name}")


if __name__ == "__main__":
    remove_uninformative_suffix()
