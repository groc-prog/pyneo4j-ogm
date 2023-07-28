"""
This module contains type definitions for query options and filters.
"""
from datetime import date, datetime, time, timedelta
from typing import Dict, List, TypedDict, Union

NumericQueryDataType = Union[int, float]
QueryDataTypes = Union[NumericQueryDataType, bool, str, bytes, datetime, date, time, timedelta]

# We need to define 5 different typed dictionaries here because the `$size` operator can only be one of the following,
# which means we have to create a Union of the five listed below to not get any more type hints if one has already been
# used.
NumericEqualsOperator = TypedDict(
    "NumericEqualsOperator",
    {
        "$eq": NumericQueryDataType,
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
        "$in": Union[QueryDataTypes, List[QueryDataTypes]],
        "$nin": Union[QueryDataTypes, List[QueryDataTypes]],
        "$all": List[QueryDataTypes],
        "$size": Union[
            NumericEqualsOperator,
            NumericGreaterThanOperator,
            NumericGreaterThanEqualsOperator,
            NumericLessThanOperator,
            NumericLessThanEqualsOperator,
            NumericQueryDataType,
        ],
        "$contains": str,
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

# We need to define different interfaces for nodes and relationships to not show invalid operants for the model type.
QueryNodeOperators = TypedDict(
    "QueryNodeOperators", {"$elementId": str, "$id": int, "$labels": Union[str, List[str]]}, total=False
)

QueryRelationshipOperators = TypedDict(
    "QueryRelationshipOperators", {"$elementId": str, "$id": int, "$type": Union[str, List[str]]}, total=False
)

# The actual interfaces used to describe query filters
NodeFilters = Union[Dict[str, QueryOperators], QueryNodeOperators]
RelationshipFilters = Union[Dict[str, QueryOperators], QueryRelationshipOperators]
