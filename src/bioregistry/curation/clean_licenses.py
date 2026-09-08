"""Standardize licenses."""

from bioregistry import Resource
from bioregistry.curation.utils import resource_mutator
from bioregistry.license_standardizer import standardize_license

__all__ = [
    "main",
]


@resource_mutator(name="standardize-licenses")
def main(resource: Resource) -> None:
    """Standardize manually curated licenses."""
    if resource.license:
        resource.license = standardize_license(resource.license, passthrough=True)
    elif license_str := resource.get_license():
        resource.license = standardize_license(license_str, passthrough=False)


if __name__ == "__main__":
    main()
