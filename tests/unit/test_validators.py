# pylint: disable=missing-module-docstring, missing-class-docstring

from pydantic import BaseModel
from pydantic.class_validators import root_validator

from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2, parse_model
from pyneo4j_ogm.queries.validators import (
    QueryOptionModel,
    _normalize_fields,
    _normalize_labels,
)

if IS_PYDANTIC_V2:
    from pydantic import model_validator


def test_normalize_fields_validator():
    class TestModel(BaseModel):
        attr: str

        if IS_PYDANTIC_V2:
            normalize_and_validate_fields = model_validator(mode="after")(  # pyright: ignore[reportUnboundVariable]
                _normalize_fields
            )
        else:
            normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

        if IS_PYDANTIC_V2:
            model_config = {
                "extra": "allow",
                "populate_by_name": True,
            }
        else:

            class Config:
                extra = "allow"

    test_model = parse_model(
        TestModel,
        {
            "attr": "bar",
            "invalid_field": "value",
            "valid_field": {"$eq": "value"},
            "invalid_operator": {"$invalid": "value"},
        },
    )

    assert hasattr(test_model, "attr")
    assert hasattr(test_model, "valid_field")
    assert not hasattr(test_model, "invalid_field")
    assert not hasattr(test_model, "invalid_operator")


def test_normalize_labels_validator():
    class TestModel(BaseModel):
        pass

    assert _normalize_labels(TestModel, None) is None
    assert _normalize_labels(TestModel, "label") == ["label"]
    assert _normalize_labels(TestModel, ["label1", "label2"]) == ["label1", "label2"]


def test_query_options_sort():
    options = QueryOptionModel(sort="name")
    assert options.sort == ["name"]

    options = QueryOptionModel(sort=["name", "age"])
    assert options.sort == ["name", "age"]
