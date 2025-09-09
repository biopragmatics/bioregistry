Reference Classes
=================

The :mod:`curies` package provides reusable building blocks for representing pre-parsed compact URIs
(CURIEs) in more complex data models with :mod:`pydantic`.

The Bioregistry extends these models using Pydantic's model validation framework (see
:func:`pydantic.model_validator`) in order to automatically standardize prefixes and local unique
identifiers against the Bioregistry database.

There are two different implementations:

1. Normalized references, which use Bioregistry's :func:`bioregistry.normalize_prefix` to create
   fully lower-case prefixes

   - :class:`bioregistry.NormalizedReference`
   - :class:`bioregistry.NormalizedNamableReference`
   - :class:`bioregistry.NormalizedNamedReference`

2. Preferred references, which use :func:`bioregistry.get_preferred_prefix` to adds case stylization
   in prefixes that often appears in semantic web applications.

   - :class:`bioregistry.StandardReference`
   - :class:`bioregistry.StandardNamableReference`
   - :class:`bioregistry.StandardNamedReference`

In the following example, the prefix is normalized to lowercase.

>>> from bioregistry import NormalizedReference
>>> NormalizedReference(prefix="oboInOwl", identifier="inSubset")
NormalizedReference(prefix='oboinowl', identifier='inSubset')

In the following example, the prefix is stylized to the preferred prefix.

>>> from bioregistry import StandardReference
>>> StandardReference(prefix="oboInOwl", identifier="inSubset")
StandardReference(prefix='oboInOwl', identifier='inSubset')
