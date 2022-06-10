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
    """
    column = _norm_column(df, column)
    results = df[column].map(
        lambda x: bioregistry.normalize_prefix(x) is not None, na_action="ignore"
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
        The optional column to put the results of validation
    """
    column = _norm_column(df, column)
    results = df[column].map(bioregistry.is_valid_curie, na_action="ignore")
    if target_column:
        df[target_column] = results
    return results


def validate_identifiers(
    df: pd.DataFrame,
    column: Union[int, str],
    prefix: str,
    target_column: Optional[str] = None,
) -> pd.Series:
    """Validate local unique identifiers in a given column.

    .. code-block:: python

        import bioregistry.pandas as brpd
        import pandas as pd

        df = pd.read_csv(
            "http://geneontology.org/gene-associations/goa_human.gaf.gz",
            sep="\t",
            comment='!',
            header=None,
        )

        # column 17: note that invalid CURIEs are written like UniProtKB:P12345-2,
        #  where these refer to isoforms and should use the prefix `uniprot.isoform`
        results = brpd.validate_identifiers(df, column="Gene Product Form ID")
    """
    column = _norm_column(df, column)
    norm_prefix = bioregistry.normalize_prefix(prefix)
    if norm_prefix is None:
        raise ValueError
    results = df[column].map(
        functools.partial(bioregistry.is_valid_identifier, prefix=norm_prefix), na_action="ignore"
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
    """Convert a column of local unique identifiers to CURIEs."""
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
            lambda s: f"{norm_prefix}:{s}", na_action="ignore"
        )
    else:  # prefix_column is not None
        prefix_column = _norm_column(df, prefix_column)
        df[[column, prefix_column]]

        raise NotImplementedError


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
