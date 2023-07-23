"""
This module contains types for options passed to the `QueryBuilder` class.
"""
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, TypedDict

TAnyExcludeListDict = bool | int | float | str | bytes | datetime | date | time | timedelta


class TypedQueryOptions(TypedDict):
    """
    Type definition for query options.
    """

    limit: int | None
    skip: int | None
    sort: List[str] | str | None
    order: str | None


TypedNodeExpression = TypedDict(
    "TypedNodeExpression",
    {"$elementId": Optional[str], "$id": Optional[int], "$patterns": Optional[List["TypedNodePatternExpression"]]},
)

TypedRelationshipExpression = TypedDict(
    "TypedRelationshipExpression",
    {
        "$elementId": Optional[str],
        "$id": Optional[int],
        "$patterns": Optional[List["TypedRelationshipPatternExpression"]],
    },
)

TypedNodeElementExpression = TypedDict(
    "TypedNodeElementExpression",
    {
        "$elementId": Optional[str],
        "$id": Optional[int],
        "$labels": Optional[List[str]],
    },
)

TypedRelationshipElementExpression = TypedDict(
    "TypedRelationshipElementExpression",
    {
        "$elementId": Optional[str],
        "$id": Optional[int],
        "$types": Optional[str | List[str]],
        "$minHops": Optional[int],
        "$maxHops": Optional[int],
    },
)

TypedNodePatternExpression = TypedDict(
    "TypedNodePatternExpression",
    {
        "$node": Optional["TypedNodeElementExpression"],
        "$direction": Optional[str],
        "$relationship": Optional["TypedRelationshipElementExpression"],
    },
)

TypedRelationshipPatternExpression = TypedDict(
    "TypedRelationshipPatternExpression",
    {
        "$startNode": Optional["TypedNodeElementExpression"],
        "$direction": Optional[str],
        "$endNode": Optional["TypedRelationshipElementExpression"],
    },
)


TypedStringComparison = TypedDict(
    "TypedStringComparison",
    {
        "$contains": Optional[str],
        "$startsWith": Optional[str],
        "$endsWith": Optional[str],
        "$regex": Optional[str],
    },
)

TypedListComparison = TypedDict(
    "TypedListComparison",
    {
        "$in": Optional[str | List[TAnyExcludeListDict]],
    },
)

TypedNumericComparison = TypedDict(
    "TypedNumericComparison",
    {
        "$gt": Optional[int | float],
        "$gte": Optional[int | float],
        "$lt": Optional[int | float],
        "$lte": Optional[int | float],
    },
)

TypedBaseComparison = TypedDict(
    "TypedBaseComparison",
    {
        "$eq": Optional[TAnyExcludeListDict],
        "$ne": Optional[TAnyExcludeListDict],
    },
)


TypedSizeComparisonExpression = TypedDict(
    "TypedComparisonExpression",
    {
        "$eq": Optional[TAnyExcludeListDict],
        "$ne": Optional[TAnyExcludeListDict],
        "$gt": Optional[int | float],
        "$gte": Optional[int | float],
        "$lt": Optional[int | float],
        "$lte": Optional[int | float],
    },
)


TypedLogicalExpression = TypedDict(
    "TypedLogicalExpression",
    {
        "$and": Optional[List["TypedCombinedExpression" | "TypedLogicalExpression"]],
        "$or": Optional[List["TypedCombinedExpression" | "TypedLogicalExpression"]],
        "$xor": Optional[List["TypedCombinedExpression" | "TypedLogicalExpression"]],
    },
)


TypedElementExpression = TypedDict(
    "TypedElementExpression",
    {
        "$elementId": Optional[str],
        "$id": Optional[int],
    },
)


TypedCombinedExpression = TypedDict(
    "TypedCombinedExpression",
    {
        "$not": Optional["TypedCombinedExpression"],
        "$all": Optional[List["TypedCombinedExpression"]],
        "$size": Optional["TypedSizeComparisonExpression"],
        "$exists": Optional[bool],
        "$eq": Optional[TAnyExcludeListDict],
        "$ne": Optional[TAnyExcludeListDict],
        "$gt": Optional[int | float],
        "$gte": Optional[int | float],
        "$lt": Optional[int | float],
        "$lte": Optional[int | float],
        "$in": Optional[List[TAnyExcludeListDict] | TAnyExcludeListDict],
        "$contains": Optional[str],
        "$startsWith": Optional[str],
        "$endsWith": Optional[str],
        "$regex": Optional[str],
        "$and": Optional[List["TypedCombinedExpression" | "TypedLogicalExpression"]],
        "$or": Optional[List["TypedCombinedExpression" | "TypedLogicalExpression"]],
        "$xor": Optional[List["TypedCombinedExpression" | "TypedLogicalExpression"]],
    },
)

TypedNodeExpressions = TypedNodeExpression | Dict[str, TypedCombinedExpression]
TypedRelationshipExpressions = TypedRelationshipExpression | Dict[str, TypedCombinedExpression]
TypedPropertyExpressions = TypedElementExpression | Dict[str, TypedCombinedExpression]
