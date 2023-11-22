"""
Pydantic validators for query operators and filters.
"""
# pylint: disable=unused-argument

from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, Extra, Field, ValidationError, root_validator, validator

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.queries.types import (
    NumericQueryDataType,
    QueryOptionsOrder,
    RelationshipMatchDirection,
)


def _normalize_fields(cls: Type[BaseModel], values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes and validates model property fields.

    Args:
        values (Dict[str, Any]): The values to normalize and validate.

    Returns:
        Dict[str, Any]: The normalized and validated values.
    """
    validated_values: Dict[str, Any] = {}

    for property_name, property_value in values.items():
        if property_name not in cls.__fields__.keys():
            try:
                validated = QueryOperatorModel.parse_obj(property_value)
                validated_value = validated.dict(
                    by_alias=True, exclude_none=True, exclude_unset=True, exclude_defaults=True
                )

                if len(validated_value.keys()) > 0:
                    validated_values[property_name] = validated_value
            except ValidationError:
                logger.debug("Invalid field %s found, omitting field", property_name)
        else:
            validated_values[property_name] = property_value

    return validated_values


def _normalize_labels(cls, value: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
    """
    Validator for `$labels` operator. If a string is passed, it will be converted to a list.

    Args:
        v (Optional[Union[str, List[str]]]): The value to validate.

    Returns:
        Optional[List[str]]: Validated value.
    """
    if isinstance(value, str):
        return [value]
    return value


class NumericEqualsOperatorModel(BaseModel):
    """
    Validator for `$eq` operator in combined use with `$size` operator.
    """

    eq_: Any = Field(alias="$eq")


class NumericNotEqualsOperatorModel(BaseModel):
    """
    Validator for `$neq` operator in combined use with `$size` operator.
    """

    neq_: Any = Field(alias="$neq")


class NumericGreaterThanOperatorModel(BaseModel):
    """
    Validator for `$gt` operator in combined use with `$size` operator.
    """

    gt_: Any = Field(alias="$gt")


class NumericGreaterThanEqualsOperatorModel(BaseModel):
    """
    Validator for `$gte` operator in combined use with `$size` operator.
    """

    gte_: Any = Field(alias="$gte")


class NumericLessThanOperatorModel(BaseModel):
    """
    Validator for `$lt` operator in combined use with `$size` operator.
    """

    lt_: Any = Field(alias="$lt")


class NumericLessThanEqualsOperatorModel(BaseModel):
    """
    Validator for `$lte` operator in combined use with `$size` operator.
    """

    lte_: Any = Field(alias="$lte")


class QueryOperatorModel(BaseModel):
    """
    Validator for query operators defined in a property.
    """

    eq_: Optional[Any] = Field(alias="$eq")
    neq_: Optional[Any] = Field(alias="$neq")
    gt_: Optional[NumericQueryDataType] = Field(alias="$gt")
    gte_: Optional[NumericQueryDataType] = Field(alias="$gte")
    lt_: Optional[NumericQueryDataType] = Field(alias="$lt")
    lte_: Optional[NumericQueryDataType] = Field(alias="$lte")
    in__: Optional[List[Any]] = Field(alias="$in")
    nin_: Optional[List[Any]] = Field(alias="$nin")
    all_: Optional[List[Any]] = Field(alias="$all")
    size_: Optional[
        Union[
            NumericQueryDataType,
            NumericNotEqualsOperatorModel,
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
    patterns_: Optional[List["PatternOperatorModel"]] = Field(alias="$patterns")

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


class RelationshipPropertyFiltersModel(BaseModel):
    """
    Validator model for relationship filters.
    """

    element_id_: Optional[str] = Field(alias="$elementId")
    id_: Optional[int] = Field(alias="$id")
    patterns_: Optional[List["PatternOperatorModel"]] = Field(alias="$patterns")
    relationship_: Optional[RelationshipFiltersModel] = Field(alias="$relationship")

    normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

    class Config:
        """
        Pydantic configuration
        """

        extra = Extra.allow
        use_enum_values = True


class PatternNodeOperatorsModel(BaseModel):
    """
    Validator model for node pattern operators.
    """

    element_id_: Optional[str] = Field(alias="$elementId")
    id_: Optional[int] = Field(alias="$id")
    labels_: Optional[Union[List[str], str]] = Field(alias="$labels")

    normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)
    normalize_and_validate_labels = validator("labels_", pre=True, allow_reuse=True)(_normalize_labels)

    class Config:
        """
        Pydantic configuration
        """

        extra = Extra.allow
        use_enum_values = True


class PatternRelationshipOperatorsModel(NodeFiltersModel):
    """
    Validator model for relationship pattern operators.
    """

    element_id_: Optional[str] = Field(alias="$elementId")
    id_: Optional[int] = Field(alias="$id")
    type_: Optional[Union[str, List[str]]] = Field(alias="$type")

    normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

    class Config:
        """
        Pydantic configuration
        """

        extra = Extra.allow
        use_enum_values = True


class PatternOperatorModel(BaseModel):
    """
    Validator for pattern operators defined in a property.
    """

    exists_: Optional[bool] = Field(default=False, alias="$exists")
    direction_: Optional[RelationshipMatchDirection] = Field(
        default=RelationshipMatchDirection.OUTGOING, alias="$direction"
    )
    node_: Optional[PatternNodeOperatorsModel] = Field(alias="$node")
    relationship_: Optional[PatternRelationshipOperatorsModel] = Field(alias="$relationship")


class MultiHopRelationshipOperatorsModel(NodeFiltersModel):
    """
    Validator model for a relationship operator in a multi hop filter.
    """

    element_id_: Optional[str] = Field(alias="$elementId")
    id_: Optional[int] = Field(alias="$id")
    type_: str = Field(alias="$type")

    normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

    class Config:
        """
        Pydantic configuration
        """

        extra = Extra.allow
        use_enum_values = True


class MultiHopNodeModel(BaseModel):
    """
    Validator model for multi hop node operators.
    """

    element_id_: Optional[str] = Field(alias="$elementId")
    id_: Optional[int] = Field(alias="$id")
    labels_: Union[List[str], str] = Field(alias="$labels")

    normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)
    normalize_and_validate_labels = validator("labels_", pre=True, allow_reuse=True)(_normalize_labels)

    class Config:
        """
        Pydantic configuration.
        """

        extra = Extra.allow
        use_enum_values = True


class MultiHopFiltersModel(BaseModel):
    """
    Validator model for node and relationship filters with multiple hops between the nodes.
    """

    min_hops_: Optional[int] = Field(alias="$minHops", ge=0, default=None)
    max_hops_: Optional[Union[int, Literal["*"]]] = Field(alias="$maxHops", ge=1, default="*")
    node_: MultiHopNodeModel = Field(alias="$node")
    relationships_: Optional[List[MultiHopRelationshipOperatorsModel]] = Field(alias="$relationships")
    direction_: Optional[RelationshipMatchDirection] = Field(
        default=RelationshipMatchDirection.OUTGOING, alias="$direction"
    )

    normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

    class Config:
        """
        Pydantic configuration.
        """

        extra = Extra.allow
        use_enum_values = True


class QueryOptionModel(BaseModel):
    """
    Validator model for query options.
    """

    limit: Optional[int] = Field(default=None, gt=0)
    skip: Optional[int] = Field(default=None, ge=0)
    sort: Optional[Union[List[str], str]] = Field(default=None)
    order: Optional[QueryOptionsOrder] = Field(default=None)

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


NodeFiltersModel.update_forward_refs()
RelationshipFiltersModel.update_forward_refs()
RelationshipPropertyFiltersModel.update_forward_refs()
MultiHopFiltersModel.update_forward_refs()
