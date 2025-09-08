"""FastAPI blueprint and routes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any

import yaml
from curies import Reference
from curies.mapping_service.utils import handle_header
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from bioregistry import Collection, Context, Manager, Registry, Resource
from bioregistry.export.rdf_export import (
    collection_to_rdf_str,
    metaresource_to_rdf_str,
    resource_to_rdf_str,
)
from bioregistry.schema import Attributable, sanitize_mapping
from bioregistry.schema_utils import (
    read_collections_contributions,
    read_prefix_contacts,
    read_prefix_contributions,
    read_prefix_reviews,
    read_registry_contributions,
)

from .utils import FORMAT_MAP, _autocomplete, _search

__all__ = [
    "api_router",
]

api_router = APIRouter(prefix="/api")


def _get_manager(request: Request) -> Manager:
    return request.app.manager  # type:ignore


DependsManager = Annotated[Manager, Depends(_get_manager)]


class UnhandledFormat(HTTPException):
    """An exception for an unhandled format."""

    def __init__(self, fmt: str) -> None:
        """Instantiate the exception.

        :param fmt: The header that was bad
        """
        super().__init__(400, f"Bad Accept header: {fmt}")


class YAMLResponse(Response):
    """A custom response encoded in YAML."""

    media_type = "application/yaml"

    def render(self, content: Any) -> bytes:
        """Render content as YAML."""
        if isinstance(content, BaseModel):
            content = content.model_dump(
                exclude_none=True,
                exclude_unset=True,
            )
        return yaml.safe_dump(
            content,
            allow_unicode=True,
            indent=2,
        ).encode("utf-8")


ACCEPT_HEADER = Header(default=None)
FORMAT_QUERY = Query(
    title="Format", default=None, description=f"The return format, one of: {list(FORMAT_MAP)}"
)
#: A mapping of mimetypes to RDFLib formats
RDF_MEDIA_TYPES = {
    "text/turtle": "turtle",
    "application/ld+json": "json-ld",
    "application/rdf+xml": "xml",
    "text/n3": "n3",
}
CONTENT_TYPE_SYNONYMS = {
    "text/json": "application/json",
    "text/yaml": "application/yaml",
}


def _handle_formats(accept: str | None, fmt: str | None) -> str:
    if fmt:
        if fmt not in FORMAT_MAP:
            raise HTTPException(
                400, f"bad query parameter format={fmt}. Should be one of {list(FORMAT_MAP)}"
            )
        return FORMAT_MAP[fmt]
    if not accept:
        return "application/json"
    for header in handle_header(accept):
        if header in CONTENT_TYPE_SYNONYMS:
            return CONTENT_TYPE_SYNONYMS[header]
        if header in RDF_MEDIA_TYPES or header in CONTENT_TYPE_SYNONYMS.values():
            return header
    return "application/json"


@api_router.get("/registry", response_model=Mapping[str, Resource], tags=["resource"])
def get_resources(
    manager: DependsManager,
    accept: str | None = ACCEPT_HEADER,
    format: str | None = FORMAT_QUERY,
) -> Response | dict[str, Resource]:
    """Get all resources."""
    accept = _handle_formats(accept, format)
    if accept == "application/json":
        return manager.registry
    elif accept == "application/yaml":
        return YAMLResponse(sanitize_mapping(manager.registry))
    elif accept in RDF_MEDIA_TYPES:
        raise NotImplementedError
    else:
        raise UnhandledFormat(accept)


@api_router.get(
    "/registry/{prefix}",
    response_model=Resource,
    tags=["resource"],
    responses={
        200: {
            "content": {
                "application/yaml": {},
                **{k: {} for k in RDF_MEDIA_TYPES},
            },
        },
    },
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def get_resource(
    manager: DependsManager,
    prefix: str = Path(
        title="Prefix", description="The Bioregistry prefix for the entry", examples=["doid"]
    ),
    accept: str = ACCEPT_HEADER,
    format: str = FORMAT_QUERY,
) -> Response | Resource:
    """Get a resource."""
    resource = manager.get_resource(prefix)
    if resource is None:
        raise HTTPException(status_code=404, detail=f"Prefix not found: {prefix}")
    resource = manager.rasterized_resource(resource)
    accept = _handle_formats(accept, format)
    if accept == "application/json":
        return resource
    elif accept == "application/yaml":
        return YAMLResponse(resource)
    elif accept in RDF_MEDIA_TYPES:
        return Response(
            resource_to_rdf_str(resource, fmt=RDF_MEDIA_TYPES[accept], manager=manager),
            media_type=accept,
        )
    else:
        raise UnhandledFormat(format)


@api_router.get(
    "/metaregistry",
    response_model=Mapping[str, Registry],
    tags=["metaresource"],
    description="Get all metaresource representing registries.",
)
def get_metaresources(
    manager: DependsManager,
    accept: str | None = ACCEPT_HEADER,
    format: str | None = FORMAT_QUERY,
) -> Response | Mapping[str, Registry]:
    """Get all registries."""
    accept = _handle_formats(accept, format)
    if accept == "application/json":
        return manager.metaregistry
    elif accept == "application/yaml":
        return YAMLResponse(sanitize_mapping(manager.metaregistry))
    elif accept in RDF_MEDIA_TYPES:
        raise NotImplementedError
    else:
        raise UnhandledFormat(accept)


METAPREFIX_PATH = Path(
    title="Metaprefix",
    description="The Bioregistry metaprefix for the external registry",
    examples=["n2t"],
)


@api_router.get(
    "/metaregistry/{metaprefix}",
    response_model=Registry,
    tags=["metaresource"],
    description="Get a metaresource representing a registry.",
    responses={
        200: {
            "content": {
                "application/yaml": {},
                **{k: {} for k in RDF_MEDIA_TYPES},
            },
        },
    },
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def get_metaresource(
    manager: DependsManager,
    metaprefix: str = METAPREFIX_PATH,
    accept: str = ACCEPT_HEADER,
    format: str = FORMAT_QUERY,
) -> Response | Registry:
    """Get all registries."""
    metaresource = manager.get_registry(metaprefix)
    if metaresource is None:
        raise HTTPException(status_code=404, detail=f"Registry not found: {metaprefix}")
    accept = _handle_formats(accept, format)
    if accept == "application/json":
        return metaresource
    elif accept == "application/yaml":
        return YAMLResponse(metaresource)
    elif accept in RDF_MEDIA_TYPES:
        return Response(
            metaresource_to_rdf_str(
                metaresource,
                fmt=RDF_MEDIA_TYPES[accept],
                manager=manager,
            ),
            media_type=accept,
        )
    else:
        raise UnhandledFormat(format)


@api_router.get(
    "/metaregistry/{metaprefix}/registry_subset.json",
    response_model=Mapping[str, Resource],
    tags=["metaresource"],
)
def get_external_registry_slim(
    manager: DependsManager,
    metaprefix: str = METAPREFIX_PATH,
) -> dict[str, Resource]:
    """Get a slim version of the registry with only resources mapped to the given external registry."""
    return {
        resource_.prefix: manager.rasterized_resource(resource_)
        for resource_ in manager.registry.values()
        if metaprefix in resource_.get_mappings()
    }


class MappingResponseMeta(BaseModel):
    """A response describing the overlap between two external registries."""

    len_overlap: int
    source: str
    target: str
    len_source_only: int
    len_target_only: int
    source_only: list[str]
    target_only: list[str]


class MappingResponse(BaseModel):
    """A response describing the overlap between two registries and their mapping."""

    meta: MappingResponseMeta
    mappings: Mapping[str, str]


@api_router.get(
    "/metaregistry/{metaprefix}/mapping/{target}",
    response_model=MappingResponse,
    tags=["metaresource"],
    description="Get mappings from the given metaresource to another",
)
def get_metaresource_external_mappings(
    manager: DependsManager,
    metaprefix: str = METAPREFIX_PATH,
    target: str = Path(title="target metaprefix"),
) -> MappingResponse | tuple[dict[str, str], int]:
    """Get mappings between two external prefixes."""
    try:
        diff = manager.get_external_mappings(metaprefix, target)
    except KeyError as e:
        return {"message": str(e)}, 400
    return MappingResponse(
        meta=MappingResponseMeta(
            len_overlap=len(diff.mappings),
            source=metaprefix,
            target=target,
            len_source_only=len(diff.source_only),
            len_target_only=len(diff.target_only),
            source_only=sorted(diff.source_only),
            target_only=sorted(diff.target_only),
        ),
        mappings=diff.mappings,
    )


@api_router.get(
    "/metaregistry/{metaprefix}/mappings.json",
    response_model=Mapping[str, str],
    tags=["metaresource"],
)
def get_metaresource_mappings(
    manager: DependsManager, metaprefix: str = METAPREFIX_PATH
) -> dict[str, str]:
    """Get mappings from the Bioregistry to an external registry."""
    if metaprefix not in manager.metaregistry:
        raise HTTPException(404, detail=f"Invalid metaprefix: {metaprefix}")
    return manager.get_registry_map(metaprefix)


@api_router.get("/collection", response_model=Mapping[str, Collection], tags=["collection"])
def get_collections(
    manager: DependsManager,
    accept: str | None = ACCEPT_HEADER,
    format: str | None = FORMAT_QUERY,
) -> Response | dict[str, Collection]:
    """Get all collections."""
    accept = _handle_formats(accept, format)
    if accept == "application/json":
        return manager.collections
    elif accept == "application/yaml":
        return YAMLResponse(sanitize_mapping(manager.collections))
    elif accept in RDF_MEDIA_TYPES:
        raise NotImplementedError
    else:
        raise HTTPException(400, f"Bad Accept header: {accept}")


@api_router.get(
    "/collection/{identifier}",
    response_model=Collection,
    tags=["collection"],
    responses={
        200: {
            "content": {
                "application/yaml": {},
                **{k: {} for k in RDF_MEDIA_TYPES},
            },
        },
    },
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def get_collection(
    manager: DependsManager,
    identifier: str = Path(
        title="Collection Identifier",
        description="The 7-digit collection identifier",
        examples=["0000001"],
    ),
    accept: str | None = ACCEPT_HEADER,
    format: str | None = FORMAT_QUERY,
) -> Response | Collection:
    """Get a collection."""
    collection = manager.collections.get(identifier)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {identifier}")
    if accept == "x-bioregistry-context" or format == "context":
        return JSONResponse(collection.as_context_jsonld())
    accept = _handle_formats(accept, format)
    if accept == "application/json":
        return collection
    elif accept == "application/yaml":
        return YAMLResponse(collection)
    elif accept in RDF_MEDIA_TYPES:
        return Response(
            collection_to_rdf_str(
                collection,
                fmt=RDF_MEDIA_TYPES[accept],
                manager=manager,
            ),
            media_type=accept,
        )
    else:
        raise HTTPException(400, f"Bad Accept header: {accept}")


@api_router.get("/context", response_model=Mapping[str, Context], tags=["context"])
def get_contexts(
    manager: DependsManager,
    accept: str | None = ACCEPT_HEADER,
    format: str | None = FORMAT_QUERY,
) -> Response | dict[str, Context]:
    """Get all context."""
    accept = _handle_formats(accept, format)
    if accept == "application/json":
        return manager.contexts
    elif accept == "application/yaml":
        return YAMLResponse(sanitize_mapping(manager.contexts))
    else:
        raise HTTPException(400, f"Bad Accept header: {accept}")


@api_router.get("/context/{identifier}", response_model=Context, tags=["context"])
def get_context(
    manager: DependsManager,
    identifier: str = Path(title="Context Key", description="The context key", examples=["obo"]),
) -> Context:
    """Get a context."""
    context: Context | None = manager.contexts.get(identifier)
    if context is None:
        raise HTTPException(status_code=404, detail=f"Context not found: {identifier}")
    return context


@api_router.get("/contributors", response_model=Mapping[str, Attributable], tags=["contributor"])
def get_contributors(
    manager: DependsManager,
    accept: str | None = ACCEPT_HEADER,
    format: str | None = FORMAT_QUERY,
) -> Response | Mapping[str, Attributable]:
    """Get all context."""
    contributors = manager.read_contributors()
    accept = _handle_formats(accept, format)
    if accept == "application/json":
        return contributors
    elif accept == "application/yaml":
        return YAMLResponse(sanitize_mapping(contributors))
    else:
        raise HTTPException(400, f"Bad Accept header: {accept}")


class ContributorResponse(BaseModel):
    """A response with information about a contributor."""

    contributor: Attributable
    prefix_contributions: set[str]
    prefix_reviews: set[str]
    prefix_contacts: set[str]
    registries: set[str]
    collections: set[str]


@api_router.get("/contributor/{orcid}", response_model=ContributorResponse, tags=["contributor"])
def get_contributor(
    manager: DependsManager,
    orcid: Annotated[str, Path(..., title="Open Researcher and Contributor Identifier")],
) -> ContributorResponse:
    """Get all context."""
    author = manager.read_contributors().get(orcid)
    if author is None:
        raise HTTPException(404, f"No contributor with orcid: {orcid}")
    return ContributorResponse(
        contributor=author,
        prefix_contributions=sorted(read_prefix_contributions(manager.registry).get(orcid, [])),
        prefix_reviews=sorted(read_prefix_reviews(manager.registry).get(orcid, [])),
        prefix_contacts=sorted(read_prefix_contacts(manager.registry).get(orcid, [])),
        registries=sorted(read_registry_contributions(manager.metaregistry).get(orcid, [])),
        collections=sorted(read_collections_contributions(manager.collections).get(orcid, [])),
    )


class IdentifierResponse(BaseModel):
    """A response for looking up a reference."""

    query: Reference
    providers: Mapping[str, str]


@api_router.get(
    "/reference/{prefix}:{identifier:path}", response_model=IdentifierResponse, tags=["reference"]
)
def get_reference(manager: DependsManager, prefix: str, identifier: str) -> IdentifierResponse:
    """Look up information on the reference."""
    # see https://fastapi.tiangolo.com/tutorial/path-params/#path-parameters-containing-paths
    # for more understanding on how the identifier:path handling works
    resource = manager.get_resource(prefix)
    if resource is None:
        raise HTTPException(404, f"invalid prefix: {prefix}")

    if not resource.is_standardizable_identifier(identifier):
        raise HTTPException(
            404,
            f"invalid identifier: {resource.get_curie(identifier)} for pattern {resource.get_pattern()}",
        )

    providers = manager.get_providers(resource.prefix, identifier)
    if not providers:
        raise HTTPException(404, f"no providers available for {resource.get_curie(identifier)}")

    return IdentifierResponse(
        query=Reference(prefix=prefix, identifier=identifier),
        providers=providers,
    )


class URIResponse(BaseModel):
    """A response for looking up a reference."""

    uri: str = Field(
        ..., description="The query URI", examples=["http://id.nlm.nih.gov/mesh/C063233"]
    )
    reference: Reference = Field(
        ...,
        description="The compact URI (CURIE)",
        examples=[Reference(prefix="mesh", identifier="C063233")],
    )
    providers: Mapping[str, str] = Field(
        ...,
        description="Equivalent URIs",
        examples=[
            {
                "default": "https://meshb.nlm.nih.gov/record/ui?ui=C063233",
                "rdf": "http://id.nlm.nih.gov/mesh/C063233",
            }
        ],
    )


class URIQuery(BaseModel):
    """A query for parsing a URI."""

    uri: str = Field(..., examples=["http://id.nlm.nih.gov/mesh/C063233"])


@api_router.post(
    "/uri/parse/", response_model=URIResponse, tags=["reference"], summary="Parse a URI"
)
def post_parse_uri(
    manager: DependsManager,
    query: Annotated[
        URIQuery, Body(..., examples=[URIQuery(uri="http://id.nlm.nih.gov/mesh/C063233")])
    ],
) -> URIResponse:
    """Parse a URI, return a CURIE, and all equivalent URIs."""
    prefix, identifier = manager.parse_uri(query.uri)
    if prefix is None or identifier is None:
        raise HTTPException(404, f"can't parse URI: {query.uri}")
    return URIResponse(
        uri=query.uri,
        reference=Reference(prefix=prefix, identifier=identifier),
        # Given the fact that we're able to parse the URI, there must be at least one provider
        providers=manager.get_providers(prefix, identifier),
    )


@api_router.get("/context.jsonld", tags=["resource"])
def generate_context_json_ld(
    manager: DependsManager,
    prefix: Annotated[
        list[str], Query(..., description="The prefix for the entry. Can be given multiple.")
    ],
) -> JSONResponse:
    """Generate an *ad-hoc* context JSON-LD file from the given parameters.

    You can either give prefixes as a comma-separated list like:

    https://bioregistry.io/api/context.jsonld?prefix=go,doid,oa

    or you can use multiple entries for "prefix" like:

    https://bioregistry.io/api/context.jsonld?prefix=go&prefix=doid&prefix=oa
    """
    prefix_map = {}
    for value in prefix:
        for prefix_ in value.split(","):
            prefix_ = manager.normalize_prefix(prefix_.strip())
            if prefix_ is None:
                continue
            uri_prefix = manager.get_uri_prefix(prefix_)
            if uri_prefix is None:
                continue
            prefix_map[prefix_] = uri_prefix

    return JSONResponse(
        {
            "@context": prefix_map,
        }
    )


@api_router.get("/autocomplete", tags=["search"])
def autocomplete(
    manager: DependsManager,
    q: Annotated[str, Query(description="A query for the prefix")],
) -> JSONResponse:
    """Complete a resolution query."""
    return JSONResponse(_autocomplete(manager, q))


@api_router.get("/search", tags=["search"])
def search(
    manager: DependsManager,
    q: Annotated[str, Query(description="A query for the prefix")],
) -> JSONResponse:
    """Search for a prefix."""
    return JSONResponse(_search(manager, q))
