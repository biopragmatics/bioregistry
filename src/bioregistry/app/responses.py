"""Response classes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import rdflib
import yaml
from fastapi.responses import Response
from pydantic import BaseModel

from ..schema import sanitize_mapping
from ..utils import registry_yaml_dumper

__all__ = [
    "TurtleResponse",
    "YAMLResponse",
]


class YAMLResponse(Response):
    """A custom response encoded in YAML."""

    media_type = "application/yaml"

    def render(self, content: BaseModel | Mapping[str, BaseModel]) -> bytes:
        """Render content as YAML."""
        data: dict[str, Any]
        if isinstance(content, BaseModel):
            data = content.model_dump(
                exclude_none=True,
                exclude_unset=True,
            )
        elif isinstance(content, dict):
            data = sanitize_mapping(content)
        else:
            raise TypeError
        return yaml.safe_dump(
            data,
            allow_unicode=True,
            indent=2,
        ).encode("utf-8")


registry_yaml_dumper()


class TurtleResponse(Response):
    """A custom response for Turtle."""

    media_type = "text/turtle"

    def render(self, content: rdflib.Graph) -> bytes:
        """Render content as YAML."""
        return content.serialize(format="ttl").encode("utf-8")
