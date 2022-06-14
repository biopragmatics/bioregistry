# -*- coding: utf-8 -*-

"""Make tables exports."""

from textwrap import dedent

import click
import pandas as pd

import bioregistry
from bioregistry.constants import (
    TABLES_GOVERNANCE_LATEX_PATH,
    TABLES_GOVERNANCE_TSV_PATH,
    TABLES_METADATA_LATEX_PATH,
    TABLES_METADATA_TSV_PATH,
    TABLES_SUMMARY_LATEX_PATH,
)
from bioregistry.summary import BioregistrySummary

__all__ = [
    "export_tables",
]

#: This is Table S2 in the paper
GOVERNANCE_COLUMNS = [
    "Registry",
    "Scope",
    "Status",
    "Imports External Prefixes",
    "Curates Novel Prefixes",
    "Accepts External Contributions",
    "Uses Public Version Control",
    "Has Public Review Team",
]


def _render_bool(x: bool, true_value: str = "✓", false_value: str = "") -> str:
    return true_value if x else false_value


def _replace_na(s: str) -> str:
    if s.lower() == "n/a":
        return ""
    return s


schema_status_map = {
    True: "✓",
    False: "",
    "required": "✓",
    "required*": "✓*",
    "present": "●",
    "present*": "●*",
    "missing": "",
    "irrelevant": "-",
    "irrelevant*": "-*",
}


def _sort_key(registry):
    if registry.prefix == "bioregistry":
        return (0, registry.prefix)
    return (1, registry.prefix)


def _get_governance_df() -> pd.DataFrame:
    rows = []
    keep_metaprefixes = set(bioregistry.count_mappings())
    for registry in sorted(bioregistry.read_metaregistry().values(), key=_sort_key):
        if registry.prefix not in keep_metaprefixes:
            continue
        rows.append(
            (
                registry.get_short_name(),
                registry.governance.scope.title(),
                registry.governance.status.title(),
                _render_bool(registry.governance.imports),
                _render_bool(registry.governance.curates),
                _render_bool(registry.governance.accepts_external_contributions),
                _render_bool(registry.governance.public_version_control),
                registry.governance.review_team_icon,
            )
        )
    return pd.DataFrame(rows, columns=GOVERNANCE_COLUMNS)


#: This is Table 2 in the paper
DATA_MODEL_CAPABILITIES = [
    ("", "Registry"),
    ("Metadata Model", "Name"),
    ("Metadata Model", "Homepage"),
    ("Metadata Model", "Desc."),
    ("Metadata Model", "Example ID"),
    ("Metadata Model", "ID Pattern"),
    ("Metadata Model", "Provider"),
    ("Metadata Model", "Alt. Providers"),
    ("Metadata Model", "Alt. Prefixes"),
    ("Metadata Model", "License"),
    ("Metadata Model", "Version"),
    ("Metadata Model", "Contact"),
    ("Capabilities and Qualities", "FAIR Data"),
    ("Capabilities and Qualities", "Search"),
    ("Capabilities and Qualities", "Prefix Provider"),
    ("Capabilities and Qualities", "Resolver"),
    ("Capabilities and Qualities", "Lookup"),
]


def _get_metadata_df() -> pd.DataFrame:
    rows = []
    keep_metaprefixes = set(bioregistry.count_mappings())
    for registry in sorted(bioregistry.read_metaregistry().values(), key=_sort_key):
        if registry.prefix not in keep_metaprefixes:
            continue
        rows.append(
            (
                registry.get_short_name(),
                *(
                    schema_status_map[t]
                    for t in (
                        registry.availability.name,
                        registry.availability.homepage,
                        registry.availability.description,
                        registry.availability.example,
                        registry.availability.pattern,
                        registry.availability.provider,
                        registry.availability.alternate_providers,
                        registry.availability.synonyms,
                        registry.availability.license,
                        registry.availability.version,
                        registry.availability.contact,
                        registry.availability.fair,
                        registry.availability.search,
                        registry.provider_uri_format is not None,
                        registry.is_resolver,
                        registry.is_lookup,
                    )
                ),
            )
        )
    return pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(DATA_MODEL_CAPABILITIES))


@click.command()
def export_tables():
    """Export tables.

    1. TODO: Export data model comparison, see also https://bioregistry.io/related#data-models
    2. Export governance comparison, see also https://bioregistry.io/related#governance
    """
    governance_df = _get_governance_df()
    governance_df.to_csv(TABLES_GOVERNANCE_TSV_PATH, sep="\t", index=False)
    TABLES_GOVERNANCE_LATEX_PATH.write_text(
        governance_df.to_latex(
            index=False,
            bold_rows=True,
            label="tab:registry-comparison-governance",
            caption=dedent(
                """\
               A survey of registries' governance and maintenance models. The scope column describes the
               kinds of prefixes contained within the registry. The status column is active if the registry
               is currently being maintained and is responsive to public external feedback, unresponsive if
               the registry is currently being maintained but is not responsive to public external feedback,
               and inactive otherwise. The imports external prefixes column denotes if the registry reuses
               and harmonizes content from external registries. The curates novel prefixes column denotes
               whether novel curation of prefixes and their associated metadata is done for the registry.
               The accepts external contributions column denotes whether the registry has both the governance
               model and technical infrastructure for accepting external contributions in the form of the
               suggestion of new prefixes, improvement to metadata associated with existing prefixes, etc.
               The uses public version control column denotes whether the data underlying the registry and/or
               its associated code are stored in a publicly accessible version-controlled system (e.g., git
               via GitHub). The has public review team column denotes whether there is a publicly accessible
               list of the reviewers. Asterisks in this column denote that rather than an explicit list, the
               reviewers can be inferred through the registry's version control system.
            """
            )
            .strip()
            .replace("\n", " "),
        ),
        encoding="utf-8",
    )

    metadata_df = _get_metadata_df()
    metadata_df.to_csv(TABLES_METADATA_TSV_PATH, sep="\t", index=False)
    metadata_caption = dedent(
        """\
        An overview on registries covering biomedical ontologies, controlled vocabularies, and databases.
        A ✓ means the field is required. A ● means it is part of the schema, but not required or incomplete
        on some entries. A blank cell means that it is not part of the metadata schema. The FAIR column denotes that a
        structured dump of the data is easily findable, accessible, and in a structured format in bulk. For
        lookup services, some fields (i.e., Example ID, Default Provider, Alternate Providers) are omitted
        because inclusion would be redundant. The search column means there is a URL into which a search
        query can be formatted to show a list of results. The provider column means there is a URL into
        which a prefix can be formatted to show a dedicated page for its metadata. *Caveats: Several of
        Wikidata's fields can be accessed indirectly with alternative SPARQL queries. BioPortal's data is
        locked behind an API that requires a key and has rate limited access. The Crop Ontology Curation Tool
        does not list homepages because it is the homepage itself. Non-english language registries in the
        OntoPortal Alliance were not included.
    """
    )
    TABLES_METADATA_LATEX_PATH.write_text(
        metadata_df.to_latex(
            index=False,
            bold_rows=True,
            label="tab:registry-comparison-governance",
            caption=metadata_caption.strip().replace("\n", " "),
        ),
        encoding="utf-8",
    )

    s = BioregistrySummary.make()
    TABLES_SUMMARY_LATEX_PATH.write_text(s.get_table_latex())


if __name__ == "__main__":
    export_tables()
