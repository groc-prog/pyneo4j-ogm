"""
This module contains pydantic models for runtime validation of operators in query expressions
and query options.
"""
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field

TAnyExcludeListDict = Union[int, float, str, bytes, bool, datetime, date, time, timedelta]


class QueryOrder(str, Enum):
    """
    Available query orders.
    """

    ASC = "ASC"
    DESC = "DESC"


class QueryOptionsValidator(BaseModel):
    """
    Validation model for query options.
    """

    limit: Optional[int] = Field(default=None, ge=1)
    skip: Optional[int] = Field(default=None, ge=0)
    sort: Optional[Union[str, list[str]]] = None
    order: Optional[QueryOrder] = None

    class Config:
        """
        Pydantic configuration options.
        """

        use_enum_values = True


class ComparisonExpressionValidator(BaseModel):
    """
    Validation model for comparison operators defined in expressions.
    """

    eq_operator: Optional[TAnyExcludeListDict] = Field(alias="$eq", extra={"parser": "{property_name} = {value}"})
    ne_operator: Optional[TAnyExcludeListDict] = Field(alias="$ne", extra={"parser": "NOT({property_name} = {value})"})
    gt_operator: Optional[Union[int, float]] = Field(alias="$gt", extra={"parser": "{property_name} > {value}"})
    gte_operator: Optional[Union[int, float]] = Field(alias="$gte", extra={"parser": "{property_name} >= {value}"})
    lt_operator: Optional[Union[int, float]] = Field(alias="$lt", extra={"parser": "{property_name} < {value}"})
    lte_operator: Optional[Union[int, float]] = Field(alias="$lte", extra={"parser": "{property_name} <= {value}"})
    in_operator: Optional[Union[List[TAnyExcludeListDict], TAnyExcludeListDict]] = Field(
        alias="$in", extra={"parser": "{property_name} IN {value}"}
    )
    contains_operator: Optional[str] = Field(alias="$contains", extra={"parser": "{property_name} CONTAINS {value}"})
    starts_with_operator: Optional[str] = Field(
        alias="$startsWith", extra={"parser": "{property_name} STARTS WITH {value}"}
    )
    ends_with_operator: Optional[str] = Field(alias="$endsWith", extra={"parser": "{property_name} ENDS WITH {value}"})
    regex_operator: Optional[str] = Field(alias="$regex", extra={"parser": "{property_name} =~ {value}"})


class LogicalExpressionValidator(BaseModel):
    """
    Validation model for logical operators defined in expressions.
    """

    and_operator: Optional[List[Union["ExpressionsValidator", "LogicalExpressionValidator"]]] = Field(
        alias="$and", extra={"parser": "AND"}
    )
    or_operator: Optional[List[Union["ExpressionsValidator", "LogicalExpressionValidator"]]] = Field(
        alias="$or", extra={"parser": "OR"}
    )
    xor_operator: Optional[List[Union["ExpressionsValidator", "LogicalExpressionValidator"]]] = Field(
        alias="$xor", extra={"parser": "XOR"}
    )


class Neo4jExpressionValidator(BaseModel):
    """
    Validation model for neo4j operators defined in expressions.
    """

    element_id_operator: Optional[str] = Field(alias="$elementId", extra={"parser": "elementId({ref}) = {value}"})
    id_operator: Optional[int] = Field(alias="$id", extra={"parser": "ID({ref}) = {value}"})


class ExpressionsValidator(Neo4jExpressionValidator, LogicalExpressionValidator, ComparisonExpressionValidator):
    """
    Validation model which combines all other validators.
    """

    not_operator: Optional["ExpressionsValidator"] = Field(alias="$not")
    all_operator: Optional[List["ExpressionsValidator"]] = Field(alias="$all")
    size_operator: Optional["ComparisonExpressionValidator"] = Field(alias="$size")
    exists_operator: Optional[bool] = Field(alias="$exists")
