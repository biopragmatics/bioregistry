"""Fix OBO PURLs as default URI prefixes."""

from bioregistry import Resource
from bioregistry.curation.utils import resource_mutator


@resource_mutator(name="standardize-obo-uris")
def fix_obo_purls(resource: Resource) -> None:
    """Fix OBO PURLs as default URI prefixes."""
    if not resource.get_obofoundry_prefix() or resource.is_deprecated() or resource.no_own_terms:
        return
    resource.uri_format = resource.get_rdf_uri_format()


if __name__ == "__main__":
    fix_obo_purls()
