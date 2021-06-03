# -*- coding: utf-8 -*-

"""Data structures.

.. seealso:: https://pydantic-docs.helpmanual.io/usage/dataclasses/#convert-stdlib-dataclasses-into-pydantic-dataclasses
"""

import json
import pathlib
from typing import List

from pydantic import BaseModel

HERE = pathlib.Path(__file__).parent.resolve()


class Author(BaseModel):
    """Metadata for an author."""

    #: The name of the author
    name: str
    #: The ORCID identifier for the author
    orcid: str


class Collection(BaseModel):
    """A collection of resources."""

    #: The collection's identifier, matching regex ^\d{7}$
    identifier: str
    #: The name of the collection
    name: str
    #: A description of the collection
    description: str
    #: A list of the resources' prefixes appearing in the collection
    resources: List[str]
    #: Authors/contributors to the collection
    authors: List[Author]


def main():
    """Dump the JSON schemata."""
    with HERE.joinpath('collection.schema.json').open('w') as file:
        json.dump(Collection.schema(), fp=file, indent=4)


if __name__ == '__main__':
    main()
