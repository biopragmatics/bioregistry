from __future__ import annotations

import bioregistry
import curies
from curies.api import ExpansionError, IdentifierStandardizationError
from pydantic import model_validator

__all__ = [
    "StandardReference",
    "StandardNamableReference",
    "StandardNamedReference"
]


def validate_identifier(values: dict[str, str]) -> dict[str, str]:  # noqa
    """Validate the identifier."""
    prefix, identifier = values.get("prefix"), values.get("identifier")
    if not prefix or not identifier:
        raise RuntimeError
    resource = bioregistry.get_resource(prefix)
    if resource is None:
        raise ExpansionError(f"Unknown prefix: {prefix}")
    values["prefix"] = resource.prefix
    if " " in identifier:
        raise IdentifierStandardizationError(f"[{prefix}] space in identifier: {identifier}")
    values["identifier"] = resource.standardize_identifier(identifier)
    if not resource.is_valid_identifier(values["identifier"]):
        raise IdentifierStandardizationError(f"non-standard identifier: {resource.prefix}:{values['identifier']}")
    return values


class StandardReference(curies.Reference):
    """An extension to :class:`curies.Reference` that automatically validates prefix and identifier."""

    @model_validator(mode="before")
    def validate_identifier(cls, values: dict[str, str]) -> dict[str, str]:  # noqa
        """Validate the identifier."""
        return validate_identifier(values)



class StandardNamableReference(StandardReference, curies.NamableReference):
    """An extension to :class:`curies.Reference` that automatically validates prefix and identifier."""

    @model_validator(mode="before")
    def validate_identifier(cls, values: dict[str, str]) -> dict[str, str]:  # noqa
        """Validate the identifier."""
        return validate_identifier(values)

class StandardNamedReference(StandardNamableReference, curies.NamedReference):
    """An extension to :class:`curies.Reference` that automatically validates prefix and identifier."""

    @model_validator(mode="before")
    def validate_identifier(cls, values: dict[str, str]) -> dict[str, str]:  # noqa
        """Validate the identifier."""
        return validate_identifier(values)
