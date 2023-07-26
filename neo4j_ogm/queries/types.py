"""
This module contains types for options passed to the `QueryBuilder` class.
"""
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Optional, TypedDict, Union

TAnyExcludeListDict = bool | int | float | str | bytes | datetime | date | time | timedelta


class RelationshipDirection(str, Enum):
    """
    Available relationship directions for pattern expressions.
    """

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    BOTH = "BOTH"


class RelationshipPropertyDirection(str, Enum):
    """
    Available relationship directions for relationship properties.
    """

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


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
        "$type": Optional[str | List[str]],
        "$minHops": Optional[int],
        "$maxHops": Optional[int],
    },
)

TypedNodePatternExpression = TypedDict(
    "TypedNodePatternExpression",
    {
        "$node": Optional[Union[TypedNodeElementExpression, Dict[str, "TypedCombinedExpression"]]],
        "$direction": Optional[RelationshipDirection],
        "$relationship": Optional[Union[TypedRelationshipElementExpression, Dict[str, "TypedCombinedExpression"]]],
        "$negate": Optional[bool],
    },
)

TypedRelationshipPatternExpression = TypedDict(
    "TypedRelationshipPatternExpression",
    {
        "$startNode": Optional[Union[TypedNodeElementExpression, Dict[str, "TypedCombinedExpression"]]],
        "$direction": Optional[RelationshipDirection],
        "$endNode": Optional[Union[TypedNodeElementExpression, Dict[str, "TypedCombinedExpression"]]],
        "$negate": Optional[bool],
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
        "$and": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
        "$or": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
        "$xor": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
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
        "$and": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
        "$or": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
        "$xor": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
    },
)

TypedNodeExpressions = Union[TypedNodeExpression, Dict[str, TypedCombinedExpression]]
TypedRelationshipExpressions = Union[TypedRelationshipExpression, Dict[str, TypedCombinedExpression]]
TypedPropertyExpressions = Union[TypedElementExpression, Dict[str, TypedCombinedExpression]]
