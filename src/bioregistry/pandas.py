"""Utilities for processing tabular data in Pandas dataframes."""

import functools
from typing import Optional, Union

import pandas as pd

import bioregistry

__all__ = [
    # Normalization
    "normalize_prefixes",
    "normalize_curies",
    # Validation
    "validate_prefixes",
    "validate_curies",
    "validate_identifiers",
    # Conversion
    "identifiers_to_curies",
    "identifiers_to_iris",
    "curies_to_iris",
    "iris_to_curies",
]


def _norm_column(df: pd.DataFrame, column: Union[int, str]) -> str:
    return column if isinstance(column, str) else df.columns[column]


def normalize_prefixes(
    df: pd.DataFrame, column: Union[int, str], target_column: Optional[str] = None
) -> None:
    """Normalize prefixes in a given column.

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = pd.read_csv(
            "http://geneontology.org/gene-associations/goa_human.gaf.gz",
            sep="\t",
            comment='!',
            header=None,
        )

        # column 1: DB
        #  i.e., `UniProtKB` becomes `uniprot`
        brpd.normalize_prefixes(df, column=0)
    """
    column = _norm_column(df, column)
    if target_column is None:
        target_column = column
    df[target_column] = df[column].map(bioregistry.normalize_prefix, na_action="ignore")


def normalize_curies(
    df: pd.DataFrame, column: Union[int, str], target_column: Optional[str] = None
) -> None:
    """Normalize CURIEs in a given column.

    :param df: A DataFrame
    :param column: The column of CURIEs to normalize
    :param target_column:
        The column to put the normalized CURIEs in. If not given, overwrites the input column in place.

    The following example shows how the entries in the widely used `Gene Ontology Annotations
    <http://geneontology.org/docs/go-annotation-file-gaf-format-2.2/#>`_ database distributed
    in the `GAF format <http://geneontology.org/docs/go-annotation-file-gaf-format-2.2/>`_ can
    be loaded with :mod:`pandas` then normalized with the Bioregistry:

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = pd.read_csv(
            "http://geneontology.org/gene-associations/goa_human.gaf.gz",
            sep="\t",
            comment='!',
            header=None,
        )

        # column 5: GO ID - fix normalization of capitalization of prefix,
        #  i.e., `GO:0003993` becomes `go:0003993`
        brpd.normalize_curies(df, column=4)

        # column 6: DB:Reference (|DB:Reference) - fix synonym of prefix
        #  i.e., `PMID:2676709` becomes `pubmed:2676709`
        brpd.normalize_curies(df, column=5)

        # column 8: With (or) From
        #  i.e., `GO:0000346` becomes `go:0000346`
        brpd.normalize_curies(df, column=7)

        # column 13: Taxon(|taxon) - fix synonym of prefix
        #  i.e., `taxon:9606` becomes `ncbitaxon:9606`
        brpd.normalize_curies(df, column=12)
    """
    column = _norm_column(df, column)
    if target_column is None:
        target_column = column
    df[target_column] = df[column].map(bioregistry.normalize_curie, na_action="ignore")


def validate_prefixes(
    df: pd.DataFrame, column: Union[int, str], target_column: Optional[str] = None
) -> pd.Series:
    """Validate prefixes in a given column.

    :param df: A DataFrame
    :param column: The column of prefixes to validate
    :param target_column:
        The optional column to put the results of validation

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = pd.read_csv(
            "http://geneontology.org/gene-associations/goa_human.gaf.gz",
            sep="\t",
            comment='!',
            header=None,
        )

        # column 1: DB
        #  i.e., `UniProtKB` entries are not standard, and are therefore false
        idx = brpd.validate_prefixes(df, column=0)

        # Slice the dataframe based on valid and invalid prefixes
        valid_prefix_df = df[idx]
        invalid_prefix_df = df[~idx]
    """
    column = _norm_column(df, column)
    results = df[column].map(
        lambda x: x == bioregistry.normalize_prefix(x), na_action="ignore"
    )
    if target_column:
        df[target_column] = results
    return results


def validate_curies(
    df: pd.DataFrame, column: Union[int, str], target_column: Optional[str] = None
) -> pd.Series:
    """Validate CURIEs in a given column.

    :param df: A DataFrame
    :param column: The column of CURIEs to validate
    :param target_column:
        The optional column to put the results of validation.

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = pd.read_csv(
            "http://geneontology.org/gene-associations/goa_human.gaf.gz",
            sep="\t",
            comment='!',
            header=None,
        )

        # column 5: GO ID - fix normalization of capitalization of prefix,
        #  i.e., `GO:0003993` is not standard and is therefore false
        idx = brpd.validate_curies(df, column=4)

        # Slice the dataframe
        valid_go_df = df[idx]
        invalid_go_df = df[~idx]
    """
    column = _norm_column(df, column)
    results = df[column].map(bioregistry.is_valid_curie, na_action="ignore")
    if target_column:
        df[target_column] = results
    return results


def validate_identifiers(
    df: pd.DataFrame,
    column: Union[int, str],
    prefix: Optional[str] = None,
    prefix_column: Optional[str] = None,
    target_column: Optional[str] = None,
) -> pd.Series:
    """Validate local unique identifiers in a given column.

    Some data sources split the prefix and identifier in separate columns,
    so you can use the ``prefix_column`` argument instead of the ``prefix``
    argument like in the following example with the GO Annotation Database:

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = pd.read_csv(
            "http://geneontology.org/gene-associations/goa_human.gaf.gz",
            sep="\t",
            comment='!',
            header=None,
        )

        # Use a combination of column 1 (DB) and column 2 (DB Object ID) for validation
        idx = brpd.validate_identifiers(df, column=1, prefix_column=0)

        # Split the dataframe based on valid and invalid identifiers
        valid_df = df[idx]
        invalid_df = df[~idx]
    """
    column = _norm_column(df, column)
    if prefix_column is None and prefix is None:
        raise ValueError
    elif prefix_column is not None and prefix is not None:
        raise ValueError
    elif prefix is not None:
        norm_prefix = bioregistry.normalize_prefix(prefix)
        if norm_prefix is None:
            raise ValueError
        results = df[column].map(
            functools.partial(bioregistry.is_valid_identifier, prefix=norm_prefix),
            na_action="ignore",
        )
    else:  # prefix_column is not None
        results = df.applymap(
            lambda row: bioregistry.is_valid_identifier(row[prefix_column], row[column]),
            na_action="ignore",
        )
    if target_column:
        df[target_column] = results
    return results


def identifiers_to_curies(
    df: pd.DataFrame,
    column: Union[int, str],
    prefix: Optional[str] = None,
    prefix_column: Optional[str] = None,
    target_column: Optional[str] = None,
) -> None:
    """Convert a column of local unique identifiers to CURIEs.

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = pd.read_csv(
            "http://geneontology.org/gene-associations/goa_human.gaf.gz",
            sep="\t",
            comment='!',
            header=None,
        )

        # column 17: Gene Product Form ID - note that invalid CURIEs are written like UniProtKB:P12345-2,
        #  where these refer to isoforms and should use the prefix `uniprot.isoform`
        idx = brpd.validate_identifiers(df, column=16)

        # Get a dataframe of the valid and invalid rows
        valid_gene_products_df = df[idx]
        invalid_gene_products_df = df[~idx]

    """
    column = _norm_column(df, column)
    if prefix_column is None and prefix is None:
        raise ValueError
    elif prefix_column is not None and prefix is not None:
        raise ValueError
    elif prefix is not None:
        norm_prefix = bioregistry.normalize_prefix(prefix)
        if norm_prefix is None:
            raise ValueError
        df[target_column or column] = df[column].map(
            functools.partial(bioregistry.curie_to_str, prefix=norm_prefix),
            na_action="ignore",
        )
    else:  # prefix_column is not None
        prefix_column = _norm_column(df, prefix_column)
        df[target_column or column] = df.applymap(
            lambda row: bioregistry.curie_to_str(row[prefix_column], row[column]),
            na_action="ignore",
        )


def identifiers_to_iris(
    df: pd.DataFrame, column: Union[int, str], prefix: str, target_column: Optional[str] = None
) -> None:
    """Convert a column of local unique identifiers to IRIs."""
    column = _norm_column(df, column)
    norm_prefix = bioregistry.normalize_prefix(prefix)
    if norm_prefix is None:
        raise ValueError
    df[target_column or column] = df[column].map(
        functools.partial(bioregistry.get_iri, prefix=norm_prefix), na_action="ignore"
    )


def curies_to_iris(
    df: pd.DataFrame, column: Union[int, str], target_column: Optional[str] = None
) -> None:
    """Convert a column of CURIEs to IRIs."""
    column = _norm_column(df, column)
    df[target_column or column] = df[column].map(bioregistry.get_iri, na_action="ignore")


def iris_to_curies(
    df: pd.DataFrame, column: Union[int, str], target_column: Optional[str] = None
) -> None:
    """Convert a column of IRIs to CURIEs."""
    column = _norm_column(df, column)
    df[target_column or column] = df[column].map(bioregistry.curie_from_iri, na_action="ignore")
