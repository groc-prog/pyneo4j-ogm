"""
Pydantic validators for query operators and filters.
"""

# pyright: reportUnboundVariable=false
# pylint: disable=unused-argument

from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, Field, ValidationError
from pydantic.class_validators import root_validator, validator

from pyneo4j_ogm.logger import logger
from pyneo4j_ogm.pydantic_utils import (
    IS_PYDANTIC_V2,
    get_model_dump,
    get_model_fields,
    parse_model,
)
from pyneo4j_ogm.queries.types import (
    NumericQueryDataType,
    QueryOptionsOrder,
    RelationshipMatchDirection,
)

if IS_PYDANTIC_V2:
    from pydantic import field_validator, model_validator


def _normalize_fields(cls: Type[BaseModel], values: Any) -> Any:
    """
    Normalizes and validates model property fields.

    Args:
        values (Any): The values to normalize and validate.

    Returns:
        Any: The normalized and validated values.
    """
    normalized_values: Dict[str, Any] = get_model_dump(values) if isinstance(values, BaseModel) else values
    validated_values: Dict[str, Any] = {}

    for property_name, property_value in normalized_values.items():
        if property_name not in get_model_fields(cls).keys():
            try:
                validated = parse_model(QueryOperatorModel, property_value)
                validated_value = get_model_dump(
                    model=validated, by_alias=True, exclude_none=True, exclude_unset=True, exclude_defaults=True
                )

                if len(validated_value.keys()) > 0:
                    validated_values[property_name] = validated_value
            except ValidationError:
                logger.debug("Invalid field %s found, omitting field", property_name)
        else:
            validated_values[property_name] = property_value

    if IS_PYDANTIC_V2:
        return cls.model_construct(**validated_values)
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


def _normalize_sort(cls, value: Optional[Union[str, List[str]]]) -> Optional[List[str]]:
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

    eq_: Optional[Any] = Field(alias="$eq", default=None)
    neq_: Optional[Any] = Field(alias="$neq", default=None)
    gt_: Optional[NumericQueryDataType] = Field(alias="$gt", default=None)
    gte_: Optional[NumericQueryDataType] = Field(alias="$gte", default=None)
    lt_: Optional[NumericQueryDataType] = Field(alias="$lt", default=None)
    lte_: Optional[NumericQueryDataType] = Field(alias="$lte", default=None)
    in__: Optional[List[Any]] = Field(alias="$in", default=None)
    nin_: Optional[List[Any]] = Field(alias="$nin", default=None)
    all_: Optional[List[Any]] = Field(alias="$all", default=None)
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
    ] = Field(alias="$size", default=None)
    contains_: Optional[str] = Field(alias="$contains", default=None)
    exists_: Optional[bool] = Field(alias="$exists", default=None)
    i_contains_: Optional[str] = Field(alias="$icontains", default=None)
    starts_with_: Optional[str] = Field(alias="$startsWith", default=None)
    i_starts_with_: Optional[str] = Field(alias="$istartsWith", default=None)
    ends_with_: Optional[str] = Field(alias="$endsWith", default=None)
    i_ends_with_: Optional[str] = Field(alias="$iendsWith", default=None)
    regex_: Optional[str] = Field(alias="$regex", default=None)
    not_: Optional["QueryOperatorModel"] = Field(alias="$not", default=None)
    and_: Optional[List["QueryOperatorModel"]] = Field(alias="$and", default=None)
    or_: Optional[List["QueryOperatorModel"]] = Field(alias="$or", default=None)
    xor_: Optional[List["QueryOperatorModel"]] = Field(alias="$xor", default=None)


class NodeFiltersModel(BaseModel):
    """
    Validator model for node filters.
    """

    element_id_: Optional[str] = Field(alias="$elementId", default=None)
    id_: Optional[int] = Field(alias="$id", default=None)
    patterns_: Optional[List["PatternOperatorModel"]] = Field(alias="$patterns", default=None)

    if IS_PYDANTIC_V2:
        normalize_and_validate_fields = model_validator(mode="after")(_normalize_fields)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


class RelationshipFiltersModel(BaseModel):
    """
    Validator model for relationship filters.
    """

    element_id_: Optional[str] = Field(alias="$elementId", default=None)
    id_: Optional[int] = Field(alias="$id", default=None)

    if IS_PYDANTIC_V2:
        normalize_and_validate_fields = model_validator(mode="after")(_normalize_fields)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


class RelationshipPropertyFiltersModel(BaseModel):
    """
    Validator model for relationship filters.
    """

    element_id_: Optional[str] = Field(alias="$elementId", default=None)
    id_: Optional[int] = Field(alias="$id", default=None)
    patterns_: Optional[List["PatternOperatorModel"]] = Field(alias="$patterns", default=None)
    relationship_: Optional[RelationshipFiltersModel] = Field(alias="$relationship", default=None)

    if IS_PYDANTIC_V2:
        normalize_and_validate_fields = model_validator(mode="after")(_normalize_fields)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


class PatternNodeOperatorsModel(BaseModel):
    """
    Validator model for node pattern operators.
    """

    element_id_: Optional[str] = Field(alias="$elementId", default=None)
    id_: Optional[int] = Field(alias="$id")
    labels_: Optional[Union[List[str], str]] = Field(alias="$labels", default=None)

    if IS_PYDANTIC_V2:
        normalize_and_validate_fields = model_validator(mode="after")(_normalize_fields)
        normalize_and_validate_labels = field_validator("labels_", mode="before")(_normalize_labels)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)
        normalize_and_validate_labels = validator("labels_", pre=True)(_normalize_labels)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


class PatternRelationshipOperatorsModel(NodeFiltersModel):
    """
    Validator model for relationship pattern operators.
    """

    element_id_: Optional[str] = Field(alias="$elementId", default=None)
    id_: Optional[int] = Field(alias="$id", default=None)
    type_: Optional[Union[str, List[str]]] = Field(alias="$type", default=None)

    if IS_PYDANTIC_V2:
        normalize_and_validate_fields = model_validator(mode="after")(_normalize_fields)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


class PatternOperatorModel(BaseModel):
    """
    Validator for pattern operators defined in a property.
    """

    exists_: bool = Field(default=False, alias="$exists")
    direction_: RelationshipMatchDirection = Field(default=RelationshipMatchDirection.OUTGOING, alias="$direction")
    node_: Optional[PatternNodeOperatorsModel] = Field(alias="$node", default=None)
    relationship_: Optional[PatternRelationshipOperatorsModel] = Field(alias="$relationship", default=None)


class MultiHopRelationshipOperatorsModel(NodeFiltersModel):
    """
    Validator model for a relationship operator in a multi hop filter.
    """

    element_id_: Optional[str] = Field(alias="$elementId", default=None)
    id_: Optional[int] = Field(alias="$id", default=None)
    type_: str = Field(alias="$type")

    if IS_PYDANTIC_V2:
        normalize_and_validate_fields = model_validator(mode="after")(_normalize_fields)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


class MultiHopNodeModel(BaseModel):
    """
    Validator model for multi hop node operators.
    """

    element_id_: Optional[str] = Field(alias="$elementId", default=None)
    id_: Optional[int] = Field(alias="$id", default=None)
    labels_: Union[List[str], str] = Field(alias="$labels")

    if IS_PYDANTIC_V2:
        normalize_and_validate_fields = model_validator(mode="after")(_normalize_fields)
        normalize_and_validate_labels = field_validator("labels_", mode="before")(_normalize_labels)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)
        normalize_and_validate_labels = validator("labels_", pre=True, allow_reuse=True)(_normalize_labels)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


class MultiHopFiltersModel(BaseModel):
    """
    Validator model for node and relationship filters with multiple hops between the nodes.
    """

    min_hops_: Optional[int] = Field(alias="$minHops", ge=0, default=None)
    max_hops_: Optional[Union[int, Literal["*"]]] = Field(alias="$maxHops", ge=1, default="*")
    node_: MultiHopNodeModel = Field(alias="$node")
    relationships_: Optional[List[MultiHopRelationshipOperatorsModel]] = Field(alias="$relationships", default=None)
    direction_: Optional[RelationshipMatchDirection] = Field(
        default=RelationshipMatchDirection.OUTGOING, alias="$direction"
    )

    if IS_PYDANTIC_V2:
        normalize_and_validate_fields = model_validator(mode="after")(_normalize_fields)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


class QueryOptionModel(BaseModel):
    """
    Validator model for query options.
    """

    limit: Optional[int] = Field(default=None, gt=0)
    skip: Optional[int] = Field(default=None, ge=0)
    sort: Optional[Union[List[str], str]] = Field(default=None)
    order: Optional[QueryOptionsOrder] = Field(default=None)

    if IS_PYDANTIC_V2:
        normalize_list_validator = field_validator("sort", mode="before")(_normalize_sort)

        model_config = {
            "extra": "allow",
            "use_enum_values": True,
        }
    else:
        normalize_list_validator = validator("sort", pre=True)(_normalize_sort)

        class Config:
            """
            Pydantic configuration
            """

            extra = "allow"
            use_enum_values = True


if IS_PYDANTIC_V2:
    NodeFiltersModel.model_rebuild()
    RelationshipFiltersModel.model_rebuild()
    RelationshipPropertyFiltersModel.model_rebuild()
    MultiHopFiltersModel.model_rebuild()
else:
    NodeFiltersModel.update_forward_refs()
    RelationshipFiltersModel.update_forward_refs()
    RelationshipPropertyFiltersModel.update_forward_refs()
    MultiHopFiltersModel.update_forward_refs()
