"""
Types used to describe queries.
"""
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from typing_extensions import NotRequired, TypedDict


class QueryOptionsOrder(str, Enum):
    """
    Enum for ordering options in a query.
    """

    ASCENDING = "ASC"
    DESCENDING = "DESC"


class RelationshipMatchDirection(str, Enum):
    """
    Enum for ordering options in a query.
    """

    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    BOTH = "BOTH"


NumericQueryDataType = Union[int, float]

# We need to define 5 different typed dictionaries here because the `$size` operator can only be
# one of the following, which means we have to create a Union of the five listed below to not get
# any more type hints if one has already been used.
NumericEqualsOperator = TypedDict(
    "NumericEqualsOperator",
    {
        "$eq": NumericQueryDataType,
    },
)

NumericNotEqualsOperator = TypedDict(
    "NumericNotEqualsOperator",
    {
        "$neq": NumericQueryDataType,
    },
)

NumericGreaterThanOperator = TypedDict(
    "NumericGreaterThanOperator",
    {
        "$gt": NumericQueryDataType,
    },
)

NumericGreaterThanEqualsOperator = TypedDict(
    "NumericGreaterThanEqualsOperator",
    {
        "$gte": NumericQueryDataType,
    },
)

NumericLessThanOperator = TypedDict(
    "NumericLessThanOperator",
    {
        "$lt": NumericQueryDataType,
    },
)

NumericLessThanEqualsOperator = TypedDict(
    "NumericLessThanEqualsOperator",
    {
        "$lte": NumericQueryDataType,
    },
)

QueryOperators = TypedDict(
    "QueryOperators",
    {
        "$eq": Optional[Any],
        "$neq": Optional[Any],
        "$gt": Optional[NumericQueryDataType],
        "$gte": Optional[NumericQueryDataType],
        "$lt": Optional[NumericQueryDataType],
        "$lte": Optional[NumericQueryDataType],
        "$in": Optional[List[Any]],
        "$nin": Optional[List[Any]],
        "$all": Optional[List[Any]],
        "$size": Optional[
            Union[
                NumericEqualsOperator,
                NumericNotEqualsOperator,
                NumericGreaterThanOperator,
                NumericGreaterThanEqualsOperator,
                NumericLessThanOperator,
                NumericLessThanEqualsOperator,
                NumericQueryDataType,
            ]
        ],
        "$contains": Optional[str],
        "$exists": Optional[bool],
        "$icontains": Optional[str],
        "$startsWith": Optional[str],
        "$istartsWith": Optional[str],
        "$endsWith": Optional[str],
        "$iendsWith": Optional[str],
        "$regex": Optional[str],
        "$not": Optional["QueryOperators"],
        "$and": Optional[List["QueryOperators"]],
        "$or": Optional[List["QueryOperators"]],
        "$xor": Optional[List["QueryOperators"]],
    },
    total=False,
)

PatternNodeOperators = TypedDict(
    "PatternNodeOperators",
    {"$elementId": Optional[str], "$id": Optional[int], "$labels": Optional[List[str]]},
    total=False,
)

PatternRelationshipOperators = TypedDict(
    "PatternRelationshipOperators",
    {"$elementId": Optional[str], "$id": Optional[int], "$type": Optional[Union[str, List[str]]]},
    total=False,
)

PatternOperator = TypedDict(
    "PatternOperator",
    {
        "$exists": Optional[bool],
        "$direction": Optional[RelationshipMatchDirection],
        "$relationship": Optional[Union[Dict[str, Union[QueryOperators, Any]], PatternRelationshipOperators]],
        "$node": Optional[Union[Dict[str, Union[QueryOperators, Any]], PatternNodeOperators]],
    },
    total=False,
)

MultiHopRelationship = TypedDict(
    "MultiHopRelationship", {"$elementId": NotRequired[Optional[str]], "$id": NotRequired[Optional[int]], "$type": str}
)

MultiHopNode = TypedDict(
    "MultiHopNode",
    {"$elementId": NotRequired[Optional[str]], "$id": NotRequired[Optional[int]], "$labels": Union[List[str], str]},
)

# We need to define different interfaces for nodes and relationships to not show invalid operants
# for the model type.
QueryNodeOperators = TypedDict(
    "QueryNodeOperators",
    {"$elementId": Optional[str], "$id": Optional[int], "$patterns": Optional[List[PatternOperator]]},
    total=False,
)

QueryRelationshipOperators = TypedDict(
    "QueryRelationshipOperators", {"$elementId": Optional[str], "$id": Optional[int]}, total=False
)

QueryRelationshipPropertyOperators = TypedDict(
    "QueryRelationshipPropertyOperators",
    {
        "$elementId": Optional[str],
        "$id": Optional[int],
        "$patterns": Optional[List[PatternOperator]],
        "$relationship": Optional[Union[Dict[str, Union[QueryOperators, Any]], QueryRelationshipOperators]],
    },
    total=False,
)

# The actual interfaces used to describe query filters
NodeFilters = Union[Dict[str, Union[QueryOperators, Any, Any]], QueryNodeOperators]
RelationshipFilters = Union[Dict[str, Union[QueryOperators, Any, Any]], QueryRelationshipOperators]
RelationshipPropertyFilters = Union[Dict[str, Union[QueryOperators, Any, Any]], QueryRelationshipPropertyOperators]

MultiHopFilters = TypedDict(
    "MultiHopFilters",
    {
        "$minHops": NotRequired[Optional[int]],
        "$maxHops": NotRequired[Optional[Union[int, Literal["*"]]]],
        "$node": Union[Dict[str, Union[QueryOperators, Any, Any]], MultiHopNode],
        "$relationships": NotRequired[
            Optional[List[Union[Dict[str, Union[QueryOperators, Any, Any]], MultiHopRelationship]]]
        ],
        "$direction": NotRequired[Optional[RelationshipMatchDirection]],
    },
)


# Interface to describe query options
class QueryOptions(TypedDict, total=False):
    """
    Interface to describe query options.
    """

    limit: Optional[int]
    skip: Optional[int]
    sort: Optional[Union[List[str], str]]
    order: Optional[QueryOptionsOrder]


# Interface for a projection
Projection = Dict[str, Union[str, Literal["$elementId"], Literal["$id"]]]
