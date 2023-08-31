from pydantic import BaseModel, Extra, root_validator

from neo4j_ogm.queries.validators import _normalize_fields, _normalize_labels


def test_normalize_fields():
    class TestModel(BaseModel):
        attr: str
        normalize_and_validate_fields = root_validator(allow_reuse=True)(_normalize_fields)

        class Config:
            extra = Extra.allow

    test_model = TestModel.parse_obj(
        {
            "attr": "bar",
            "invalid_field": "value",
            "valid_field": {"$eq": "value"},
            "invalid_operator": {"$invalid": "value"},
        }
    )

    assert hasattr(test_model, "attr")
    assert hasattr(test_model, "valid_field")
    assert not hasattr(test_model, "invalid_field")
    assert not hasattr(test_model, "invalid_operator")


def test_normalize_labels():
    class TestModel(BaseModel):
        pass

    assert _normalize_labels(TestModel, None) is None
    assert _normalize_labels(TestModel, "label") == ["label"]
    assert _normalize_labels(TestModel, ["label1", "label2"]) == ["label1", "label2"]
