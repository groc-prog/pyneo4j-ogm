"""
This module contains pydantic models for validating and normalizing query filters.
"""
import logging
from copy import deepcopy
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Extra, Field, ValidationError, root_validator, validator

from neo4j_ogm.queries.types import NumericQueryDataType, QueryDataTypes, QueryOptionsOrder


def _normalize_fields(cls: BaseModel, values: Dict[str, Any]) -> Dict[str, Any]:
    validated_values: Dict[str, Any] = deepcopy(values)

    for property_name, property_value in values.items():
        if property_name not in cls.__fields__.keys():
            try:
                validated = QueryOperatorModel.parse_obj(property_value)
                validated_values[property_name] = validated.dict(by_alias=True, exclude_none=True, exclude_unset=True)
            except ValidationError:
                validated_values.pop(property_name)
                logging.debug("Invalid field %s found, omitting field", property_name)

    return validated_values


class NumericEqualsOperatorModel(BaseModel):
    """
    Validator for `$eq` operator in combined use with `$size` operator.
    """

    eq_: QueryDataTypes = Field(alias="$eq")


class NumericGreaterThanOperatorModel(BaseModel):
    """
    Validator for `$gt` operator in combined use with `$size` operator.
    """

    gt_: QueryDataTypes = Field(alias="$gt")


class NumericGreaterThanEqualsOperatorModel(BaseModel):
    """
    Validator for `$gte` operator in combined use with `$size` operator.
    """

    gte_: QueryDataTypes = Field(alias="$gte")


class NumericLessThanOperatorModel(BaseModel):
    """
    Validator for `$lt` operator in combined use with `$size` operator.
    """

    lt_: QueryDataTypes = Field(alias="$lt")


class NumericLessThanEqualsOperatorModel(BaseModel):
    """
    Validator for `$lte` operator in combined use with `$size` operator.
    """

    lte_: QueryDataTypes = Field(alias="$lte")


class QueryOperatorModel(BaseModel):
    """
    Validator for query operators defined in a property.
    """

    eq_: Optional[QueryDataTypes] = Field(alias="$eq")
    neq_: Optional[QueryDataTypes] = Field(alias="$neq")
    gt_: Optional[NumericQueryDataType] = Field(alias="$gt")
    gte_: Optional[NumericQueryDataType] = Field(alias="$gte")
    lt_: Optional[NumericQueryDataType] = Field(alias="$lt")
    lte_: Optional[NumericQueryDataType] = Field(alias="$lte")
    in__: Optional[Union[QueryDataTypes, List[QueryDataTypes]]] = Field(alias="$in")
    nin_: Optional[Union[QueryDataTypes, List[QueryDataTypes]]] = Field(alias="$nin")
    all_: Optional[List[QueryDataTypes]] = Field(alias="$all")
    size_: Optional[
        Union[
            NumericQueryDataType,
            NumericEqualsOperatorModel,
            NumericGreaterThanOperatorModel,
            NumericGreaterThanEqualsOperatorModel,
            NumericLessThanOperatorModel,
            NumericLessThanEqualsOperatorModel,
        ]
    ] = Field(alias="$size")
    contains_: Optional[str] = Field(alias="$contains")
    exists_: Optional[bool] = Field(alias="$exists")
    i_contains_: Optional[str] = Field(alias="$icontains")
    starts_with_: Optional[str] = Field(alias="$startsWith")
    i_starts_with_: Optional[str] = Field(alias="$istartsWith")
    ends_with_: Optional[str] = Field(alias="$endsWith")
    i_ends_with_: Optional[str] = Field(alias="$iendsWith")
    regex_: Optional[str] = Field(alias="$regex")
    not_: Optional["QueryOperatorModel"] = Field(alias="$not")
    and_: Optional[List["QueryOperatorModel"]] = Field(alias="$and")
    or_: Optional[List["QueryOperatorModel"]] = Field(alias="$or")
    xor_: Optional[List["QueryOperatorModel"]] = Field(alias="$xor")


class NodeFiltersModel(BaseModel):
    """
    Validator model for node filters.
    """

    element_id_: Optional[str] = Field(alias="$elementId")
    id_: Optional[int] = Field(alias="$id")

    normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

    class Config:
        """
        Pydantic configuration
        """

        extra = Extra.allow
        use_enum_values = True


class RelationshipFiltersModel(BaseModel):
    """
    Validator model for relationship filters.
    """

    element_id_: Optional[str] = Field(alias="$elementId")
    id_: Optional[int] = Field(alias="$id")

    normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

    class Config:
        """
        Pydantic configuration
        """

        extra = Extra.allow
        use_enum_values = True


class QueryOptionModel(BaseModel):
    """
    Validator model for query options.
    """

    limit: Optional[int]
    skip: Optional[int]
    sort: Optional[List[str]]
    order: Optional[QueryOptionsOrder]

    @validator("sort", pre=True)
    def sort_to_list(cls, value: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
        """
        Validator for `sort` option. If a string is passed, it will be converted to a list.

        Args:
            v (Optional[Union[str, List[str]]]): The value to validate.

        Returns:
            Optional[List[str]]: Validated value.
        """
        if isinstance(value, str):
            return [value]
        return value

    class Config:
        """
        Pydantic configuration.
        """

        use_enum_values = True
