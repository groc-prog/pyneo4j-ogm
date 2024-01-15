# pylint: disable=invalid-name, redefined-outer-name, unused-import, missing-module-docstring, missing-class-docstring

from pyneo4j_ogm.pydantic_utils import IS_PYDANTIC_V2, get_schema
from tests.fixtures.db_setup import Coffee, Consumed, Developer
from tests.utils.string_utils import assert_string_equality


def test_schema():
    setattr(Developer, "_client", None)
    setattr(Coffee, "_client", None)
    setattr(Consumed, "_client", None)

    schema = get_schema(Developer)

    if IS_PYDANTIC_V2:
        assert "coffee" in schema["properties"]
        assert "default" in schema["properties"]["coffee"]
        assert_string_equality(
            schema["properties"]["coffee"]["default"],
            """RelationshipProperty(target_model_name=Coffee, relationship_model=Consumed,
            direction=OUTGOING, cardinality=ZERO_OR_MORE,
            allow_multiple=False)""",
        )
        assert schema["properties"]["coffee"]["type"] == "object"
        assert schema["properties"]["coffee"]["title"] == "Coffee"
        assert schema["properties"]["coffee"]["required"] == [
            "target_model_name",
            "relationship_model_name",
            "direction",
        ]
        assert schema["properties"]["coffee"]["properties"]["target_model_name"]["type"] == "string"
        assert schema["properties"]["coffee"]["properties"]["relationship_model_name"]["type"] == "string"
        assert schema["properties"]["coffee"]["properties"]["direction"]["type"] == "string"
        assert schema["properties"]["coffee"]["properties"]["cardinality"]["type"] == "string"
        assert schema["properties"]["coffee"]["properties"]["allow_multiple"]["type"] == "boolean"

        assert "colleagues" in schema["properties"]
        assert "default" in schema["properties"]["colleagues"]
        assert_string_equality(
            schema["properties"]["colleagues"]["default"],
            """RelationshipProperty(target_model_name=Developer, relationship_model=WorkedWith,
            direction=OUTGOING, cardinality=ZERO_OR_MORE,
            allow_multiple=True)""",
        )
        assert schema["properties"]["colleagues"]["type"] == "object"
        assert schema["properties"]["colleagues"]["title"] == "Colleagues"
        assert schema["properties"]["colleagues"]["required"] == [
            "target_model_name",
            "relationship_model_name",
            "direction",
        ]
        assert schema["properties"]["colleagues"]["properties"]["target_model_name"]["type"] == "string"
        assert schema["properties"]["colleagues"]["properties"]["relationship_model_name"]["type"] == "string"
        assert schema["properties"]["colleagues"]["properties"]["direction"]["type"] == "string"
        assert schema["properties"]["colleagues"]["properties"]["cardinality"]["type"] == "string"
        assert schema["properties"]["colleagues"]["properties"]["allow_multiple"]["type"] == "boolean"
    else:
        assert "coffee" in schema["definitions"]["Developer"]["properties"]
        assert "default" in schema["definitions"]["Developer"]["properties"]["coffee"]
        assert_string_equality(
            schema["definitions"]["Developer"]["properties"]["coffee"]["default"],
            """RelationshipProperty(target_model_name=Coffee, relationship_model=Consumed,
            direction=OUTGOING, cardinality=ZERO_OR_MORE,
            allow_multiple=False)""",
        )
        assert schema["definitions"]["Developer"]["properties"]["coffee"]["type"] == "object"
        assert schema["definitions"]["Developer"]["properties"]["coffee"]["title"] == "Coffee"
        assert schema["definitions"]["Developer"]["properties"]["coffee"]["required"] == [
            "target_model_name",
            "relationship_model_name",
            "direction",
        ]
        assert (
            schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["target_model_name"]["type"]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["relationship_model_name"]["type"]
            == "string"
        )
        assert schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["direction"]["type"] == "string"
        assert (
            schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["cardinality"]["type"] == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["coffee"]["properties"]["allow_multiple"]["type"]
            == "boolean"
        )

        assert "colleagues" in schema["definitions"]["Developer"]["properties"]
        assert "default" in schema["definitions"]["Developer"]["properties"]["colleagues"]
        assert_string_equality(
            schema["definitions"]["Developer"]["properties"]["colleagues"]["default"],
            """RelationshipProperty(target_model_name=Developer, relationship_model=WorkedWith,
            direction=OUTGOING, cardinality=ZERO_OR_MORE,
            allow_multiple=True)""",
        )
        assert schema["definitions"]["Developer"]["properties"]["colleagues"]["type"] == "object"
        assert schema["definitions"]["Developer"]["properties"]["colleagues"]["title"] == "Colleagues"
        assert schema["definitions"]["Developer"]["properties"]["colleagues"]["required"] == [
            "target_model_name",
            "relationship_model_name",
            "direction",
        ]
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["target_model_name"]["type"]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["relationship_model_name"][
                "type"
            ]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["direction"]["type"]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["cardinality"]["type"]
            == "string"
        )
        assert (
            schema["definitions"]["Developer"]["properties"]["colleagues"]["properties"]["allow_multiple"]["type"]
            == "boolean"
        )
