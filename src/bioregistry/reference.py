"""Extensions to :class:`curies.Reference` that incorporate either Bioregistry normalization or standardization."""

from __future__ import annotations

import curies
from curies.api import ExpansionError, IdentifierStandardizationError
from pydantic import model_validator

import bioregistry

__all__ = [
    "NormalizedNamableReference",
    "NormalizedNamedReference",
    "NormalizedReference",
    "StandardNamableReference",
    "StandardNamedReference",
    "StandardReference",
]


def _normalize_values(values: dict[str, str] | str) -> dict[str, str]:
    """Validate the identifier."""
    if isinstance(values, str):
        prefix_, _, identifier_ = values.partition(":")
        if not identifier_:
            raise ValueError("not formatted as a CURIE")
        values = {"prefix": prefix_, "identifier": identifier_}
    prefix, identifier = values.get("prefix"), values.get("identifier")
    if prefix is None or identifier is None:
        raise RuntimeError(f"missing prefix/identifier from values: {values}")
    resource = bioregistry.get_resource(prefix)
    if resource is None:
        raise ExpansionError(f"Unknown prefix: {prefix}")
    values["prefix"] = resource.prefix
    if " " in identifier:
        raise IdentifierStandardizationError(f"[{prefix}] space in identifier: {identifier}")
    values["identifier"] = resource.standardize_identifier(identifier)
    if not resource.is_valid_identifier(values["identifier"]):
        raise IdentifierStandardizationError(
            f"non-standard identifier: {resource.prefix}:{values['identifier']}"
        )
    return values


def _standardize_values(values: dict[str, str] | str) -> dict[str, str]:
    """Validate the identifier."""
    if isinstance(values, str):
        prefix_, _, identifier_ = values.partition(":")
        if not identifier_:
            raise ValueError("not formatted as a CURIE")
        values = {"prefix": prefix_, "identifier": identifier_}
    prefix, identifier = values.get("prefix"), values.get("identifier")
    if prefix is None or identifier is None:
        raise RuntimeError(f"missing prefix/identifier from values: {values}")
    resource = bioregistry.get_resource(prefix)
    if resource is None:
        raise ExpansionError(f"Unknown prefix: {prefix}")
    values["prefix"] = resource.get_preferred_prefix() or resource.prefix
    if " " in identifier:
        raise IdentifierStandardizationError(f"[{prefix}] space in identifier: {identifier}")
    values["identifier"] = resource.standardize_identifier(identifier)
    if not resource.is_valid_identifier(values["identifier"]):
        raise IdentifierStandardizationError(
            f"non-standard identifier: {resource.prefix}:{values['identifier']}. "
            f"Does not match pattern {resource.get_pattern()}"
        )
    return values


class NormalizedReference(curies.Reference):
    """Extends :class:`curies.Reference` to normalize the prefix against the Bioregistry.

    >>> NormalizedReference(prefix="go", identifier="0032571")
    NormalizedReference(prefix='go', identifier='0032571')

    With a name:

    >>> NormalizedReference(prefix="go", identifier="0032571")
    NormalizedReference(prefix='go', identifier='0032571')

    Standardizes capitalization to lowercase:

    >>> NormalizedReference(prefix="GO", identifier="0032571")
    NormalizedReference(prefix='go', identifier='0032571')

    Standardizes prefix synonyms to lowercase:

    >>> NormalizedReference(prefix="GOBP", identifier="0032571")
    NormalizedReference(prefix='go', identifier='0032571')

    If you're deriving a model, then pass a string, this can still work

    >>> from pydantic import BaseModel
    >>> class Derived(BaseModel):
    ...     reference: NormalizedReference
    >>> Derived(reference="go:0032571")
    Derived(reference=NormalizedReference(prefix='go', identifier='0032571'))

    """

    @model_validator(mode="before")
    def validate_identifier(cls, values: dict[str, str] | str) -> dict[str, str]:  # noqa
        """Validate the identifier."""
        return _normalize_values(values)


class NormalizedNamableReference(NormalizedReference, curies.NamableReference):
    """Extends :class:`curies.NamableReference` to normalize the prefix against the Bioregistry.

    >>> NormalizedNamedReference(prefix="go", identifier="0032571")
    NormalizedNamedReference(prefix='go', identifier='0032571', name=None)

    With a name:

    >>> NormalizedNamedReference(prefix="go", identifier="0032571", name="response to vitamin K")
    NormalizedNamedReference(prefix='go', identifier='0032571', name='response to vitamin K')

    Standardizes capitalization to lowercase:

    >>> NormalizedNamedReference(prefix="GO", identifier="0032571", name="response to vitamin K")
    NormalizedNamedReference(prefix='go', identifier='0032571', name='response to vitamin K')

    Standardizes prefix synonyms to lowercase:

    >>> NormalizedNamedReference(prefix="GOBP", identifier="0032571", name="response to vitamin K")
    NormalizedNamedReference(prefix='go', identifier='0032571', name='response to vitamin K')
    """


class NormalizedNamedReference(NormalizedNamableReference, curies.NamedReference):
    """Extends :class:`curies.NamedReference` to normalize the prefix against the Bioregistry.

    >>> NormalizedNamedReference(prefix="go", identifier="0032571", name="response to vitamin K")
    NormalizedNamedReference(prefix='go', identifier='0032571', name='response to vitamin K')

    Standardizes capitalization to lowercase:

    >>> NormalizedNamedReference(prefix="GO", identifier="0032571", name="response to vitamin K")
    NormalizedNamedReference(prefix='go', identifier='0032571', name='response to vitamin K')

    Standardizes prefix synonyms to lowercase:

    >>> NormalizedNamedReference(prefix="GOBP", identifier="0032571", name="response to vitamin K")
    NormalizedNamedReference(prefix='go', identifier='0032571', name='response to vitamin K')
    """


class StandardReference(curies.Reference):
    """An extension to :class:`curies.Reference` that automatically validates prefix and identifier.

    >>> StandardReference(prefix="GO", identifier="0032571")
    StandardReference(prefix='GO', identifier='0032571')

    Standardizes capitalization to preferred prefix:

    >>> StandardReference(prefix="go", identifier="0032571")
    StandardReference(prefix='GO', identifier='0032571')

    Standardizes prefix synonyms to lowercase:

    >>> StandardReference(prefix="GOBP", identifier="0032571")
    StandardReference(prefix='GO', identifier='0032571')

    If you're deriving a model, then pass a string, this can still work

    >>> from pydantic import BaseModel
    >>> class Derived(BaseModel):
    ...     reference: StandardReference
    >>> Derived(reference="go:0032571")
    Derived(reference=StandardReference(prefix='GO', identifier='0032571'))

    """

    @model_validator(mode="before")
    def validate_identifier(cls, values: dict[str, str] | str) -> dict[str, str]:  # noqa
        """Validate the identifier."""
        return _standardize_values(values)


class StandardNamableReference(StandardReference, curies.NamableReference):
    """An extension to :class:`curies.NamableReference` that automatically validates prefix and identifier.

    >>> StandardNamableReference(prefix="GO", identifier="0032571")
    StandardNamableReference(prefix='GO', identifier='0032571', name=None)

    With a name:

    >>> StandardNamableReference(prefix="GO", identifier="0032571", name="response to vitamin K")
    StandardNamableReference(prefix='GO', identifier='0032571', name='response to vitamin K')

    Standardizes capitalization to preferred prefix:

    >>> StandardNamableReference(prefix="go", identifier="0032571", name="response to vitamin K")
    StandardNamableReference(prefix='GO', identifier='0032571', name='response to vitamin K')

    Standardizes prefix synonyms to lowercase:

    >>> StandardNamableReference(prefix="GOBP", identifier="0032571", name="response to vitamin K")
    StandardNamableReference(prefix='GO', identifier='0032571', name='response to vitamin K')
    """


class StandardNamedReference(StandardNamableReference, curies.NamedReference):
    """An extension to :class:`curies.NamedReference` that automatically validates prefix and identifier.

    >>> StandardNamedReference(prefix="GO", identifier="0032571", name="response to vitamin K")
    StandardNamedReference(prefix='GO', identifier='0032571', name='response to vitamin K')

    Standardizes capitalization to preferred prefix:

    >>> StandardNamedReference(prefix="go", identifier="0032571", name="response to vitamin K")
    StandardNamedReference(prefix='GO', identifier='0032571', name='response to vitamin K')

    Standardizes prefix synonyms to lowercase:

    >>> StandardNamedReference(prefix="GOBP", identifier="0032571", name="response to vitamin K")
    StandardNamedReference(prefix='GO', identifier='0032571', name='response to vitamin K')
    """
