"""
This module contains types for options passed to the `QueryBuilder` class.
"""
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, TypedDict, Union

TAnyExcludeListDict = Union[bool, int, float, str, bytes, datetime, date, time, timedelta]


class TypedQueryOptions(TypedDict):
    """
    Type definition for query options.
    """

    limit: int | None
    skip: int | None
    sort: list[str] | str | None
    order: str | None


TypedComparisonExpression = TypedDict(
    "TypedComparisonExpression",
    {
        "$eq": Optional[TAnyExcludeListDict],
        "$ne": Optional[TAnyExcludeListDict],
        "$gt": Optional[Union[int, float]],
        "$gte": Optional[Union[int, float]],
        "$lt": Optional[Union[int, float]],
        "$lte": Optional[Union[int, float]],
        "$in": Optional[Union[List[TAnyExcludeListDict], TAnyExcludeListDict]],
        "$contains": Optional[str],
        "$startsWith": Optional[str],
        "$endsWith": Optional[str],
        "$regex": Optional[str],
    },
)


TypedSizeComparisonExpression = TypedDict(
    "TypedComparisonExpression",
    {
        "$eq": Optional[TAnyExcludeListDict],
        "$ne": Optional[TAnyExcludeListDict],
        "$gt": Optional[Union[int, float]],
        "$gte": Optional[Union[int, float]],
        "$lt": Optional[Union[int, float]],
        "$lte": Optional[Union[int, float]],
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


TypedNeo4jExpression = TypedDict(
    "TypedNeo4jExpression",
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
        "$size": Optional[TypedSizeComparisonExpression],
        "$exists": Optional[bool],
        "$eq": Optional[TAnyExcludeListDict],
        "$ne": Optional[TAnyExcludeListDict],
        "$gt": Optional[Union[int, float]],
        "$gte": Optional[Union[int, float]],
        "$lt": Optional[Union[int, float]],
        "$lte": Optional[Union[int, float]],
        "$in": Optional[Union[List[TAnyExcludeListDict], TAnyExcludeListDict]],
        "$contains": Optional[str],
        "$startsWith": Optional[str],
        "$endsWith": Optional[str],
        "$regex": Optional[str],
        "$and": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
        "$or": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
        "$xor": Optional[List[Union["TypedCombinedExpression", "TypedLogicalExpression"]]],
    },
)

TypedNeo4jExpressions = TypedDict(
    "TypedNeo4jExpressions",
    {"$elementId": Optional[str], "$id": Optional[int]},
)

TypedRelationshipTypePatternExpressions = TypedDict(
    "TypedRelationshipTypePatternExpressions",
    {"$type": Optional[str]},
)

TypedNodeLabelsPatternExpressions = TypedDict(
    "TypedNodeLabelsPatternExpressions",
    {"$labels": Optional[List[str]]},
)

TypedCombinedPatternExpressions = TypedDict(
    "TypedCombinedPatternExpressions",
    {
        "$direction": Optional[str],
        "$node": Optional[
            Union[TypedNodeLabelsPatternExpressions, TypedNeo4jExpressions, Dict[str, TypedCombinedExpression]]
        ],
        "$relationship": Optional[
            Union[TypedRelationshipTypePatternExpressions, TypedNeo4jExpressions, Dict[str, TypedCombinedExpression]]
        ],
    },
)

TypedPatternExpressions = TypedDict("TypedPatternExpressions", {"$pattern": List[TypedCombinedPatternExpressions]})


TypedExpressions = Union[TypedPatternExpressions, TypedNeo4jExpressions, Dict[str, TypedCombinedExpression]]
