"""
This module contains types for options passed to the `QueryBuilder` class.
"""
from typing import TypedDict


class TypedQueryOptions(TypedDict):
    """
    Type definition for query options.
    """

    limit: int | None
    skip: int | None
    sort: list[str] | str | None
    order: str | None
