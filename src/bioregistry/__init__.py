# -*- coding: utf-8 -*-

"""Extract registry information."""

from .resolve import (  # noqa
    get, get_banana, get_description, get_email, get_example, get_format, get_homepage, get_identifiers_org_prefix,
    get_mappings, get_name, get_obo_download, get_owl_download, get_pattern, get_pattern_re, get_registry,
    get_registry_description, get_registry_homepage, get_registry_name, get_registry_url, get_synonyms, get_version,
    get_versions, has_terms, is_deprecated, namespace_in_lui, normalize_prefix, parse_curie,
)
from .resolve_identifier import (# noqa
    get_bioportal_url, get_identifiers_org_curie, get_identifiers_org_url, get_link, get_n2t_url, get_obofoundry_link,
    get_ols_link, get_providers, get_providers_list, get_registry_resolve_url, validate,
)
from .utils import read_bioregistry, read_metaregistry  # noqa
