"""
Types used to describe queries.
"""
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Dict, List, Literal, Optional, TypedDict, Union


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
QueryDataTypes = Union[bool, NumericQueryDataType, str, bytes, datetime, date, time, timedelta]

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
    "NumericEqualsOperator",
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
        "$eq": QueryDataTypes,
        "$neq": QueryDataTypes,
        "$gt": NumericQueryDataType,
        "$gte": NumericQueryDataType,
        "$lt": NumericQueryDataType,
        "$lte": NumericQueryDataType,
        "$in": List[QueryDataTypes],
        "$nin": List[QueryDataTypes],
        "$all": List[QueryDataTypes],
        "$size": Union[
            NumericEqualsOperator,
            NumericNotEqualsOperator,
            NumericGreaterThanOperator,
            NumericGreaterThanEqualsOperator,
            NumericLessThanOperator,
            NumericLessThanEqualsOperator,
            NumericQueryDataType,
        ],
        "$contains": str,
        "$exists": bool,
        "$icontains": str,
        "$startsWith": str,
        "$istartsWith": str,
        "$endsWith": str,
        "$iendsWith": str,
        "$regex": str,
        "$not": "QueryOperators",
        "$and": List["QueryOperators"],
        "$or": List["QueryOperators"],
        "$xor": List["QueryOperators"],
    },
    total=False,
)

PatternNodeOperators = TypedDict(
    "PatternNodeElementOperators",
    {"$elementId": str, "$id": int, "$labels": List[str]},
    total=True,
)

PatternRelationshipOperators = TypedDict(
    "PatternRelationshipElementOperators",
    {"$elementId": str, "$id": int, "$type": Union[str, List[str]]},
    total=True,
)

NodePattern = Union[Dict[str, Union[QueryOperators, QueryDataTypes]], PatternNodeOperators]
RelationshipPattern = Union[Dict[str, Union[QueryOperators, QueryDataTypes]], PatternRelationshipOperators]

PatternOperator = TypedDict(
    "PatternOperator",
    {
        "$exists": bool,
        "$direction": RelationshipMatchDirection,
        "$relationship": RelationshipPattern,
        "$node": NodePattern,
    },
    total=False,
)


MultiHopRelationship = TypedDict(
    "MultiHopRelationship", {"$elementId": Optional[str], "$id": Optional[int], "$type": str}, total=False
)

# We need to define different interfaces for nodes and relationships to not show invalid operants
# for the model type.
QueryNodeOperators = TypedDict(
    "QueryNodeOperators",
    {"$elementId": str, "$id": int, "$patterns": List[PatternOperator]},
    total=False,
)

QueryRelationshipOperators = TypedDict("QueryRelationshipOperators", {"$elementId": str, "$id": int}, total=False)

QueryRelationshipPropertyOperators = TypedDict(
    "QueryRelationshipPropertyOperators",
    {
        "$elementId": str,
        "$id": int,
        "$patterns": List[PatternOperator],
        "$relationship": Union[Dict[str, Union[QueryOperators, QueryDataTypes]], QueryRelationshipOperators],
    },
    total=False,
)

MultiHopNode = TypedDict(
    "MultiHopNode",
    {"$elementId": Optional[str], "$id": Optional[int], "$labels": List[str]},
    total=False,
)

# The actual interfaces used to describe query filters
NodeFilters = Union[Dict[str, Union[QueryOperators, QueryDataTypes]], QueryNodeOperators]
RelationshipFilters = Union[Dict[str, Union[QueryOperators, QueryDataTypes]], QueryRelationshipOperators]
RelationshipPropertyFilters = Union[
    Dict[str, Union[QueryOperators, QueryDataTypes]], QueryRelationshipPropertyOperators
]

MultiHopFilters = TypedDict(
    "MultiHopFilters",
    {
        "$minHops": Optional[int],
        "$maxHops": Optional[Union[int, Literal["*"]]],
        "$node": Union[Dict[str, Union[QueryOperators, QueryDataTypes]], MultiHopNode],
        "$relationships": Optional[List[Union[Dict[str, Union[QueryOperators, QueryDataTypes]], MultiHopRelationship]]],
    },
    total=False,
)


# Interface to describe query options
class QueryOptions(TypedDict, total=False):
    """
    Interface to describe query options.
    """

    limit: int
    skip: int
    sort: Union[List[str], str]
    order: str
