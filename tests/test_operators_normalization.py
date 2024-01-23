# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from pyneo4j_ogm.queries.operators import Operators
from tests.fixtures.operators_builder import operators_builder


def test_normalize_expressions(operators_builder: Operators):
    # Test if key-value pairs without operators are converted to $eq
    expression = {"name": "John"}
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {"name": {"$eq": "John"}}

    # Test if `$not` and `$size` operators without a nested operator
    # are converted to `$eq`
    expression = {"name": {"$not": "John"}}
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {"name": {"$not": {"$eq": "John"}}}

    expression = {"friends": {"$size": 2}}
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {"friends": {"$size": {"$eq": 2}}}

    # Test if multiple defined operators get combined into a single `$and` operator
    # and multiple operators on different keys stay the same
    expression = {"name": {"$neq": "John", "$icontains": "doe"}}
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {"name": {"$and": [{"$neq": "John"}, {"$icontains": "doe"}]}}

    expression = {"name": "John", "age": {"$gt": 18}}
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {"name": {"$eq": "John"}, "age": {"$gt": 18}}

    # Test if nested operators get normalized
    expression = {"$or": [{"name": "John"}, {"name": "Jane"}]}
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {"$or": [{"name": {"$eq": "John"}}, {"name": {"$eq": "Jane"}}]}

    # Test pattern expressions for `$nodes` and `$relationship` operators
    expression = {"$patterns": [{"$node": {"name": "John"}}, {"$relationship": {"name": "Jane"}}]}
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {
        "$patterns": [{"$node": {"name": {"$eq": "John"}}}, {"$relationship": {"name": {"$eq": "Jane"}}}]
    }

    # Test normalizations for `$node` and `$relationships` operators
    expression = {"$node": {"name": "Jane", "age": {"$lte": 12}}}
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {"$node": {"name": {"$eq": "Jane"}, "age": {"$lte": 12}}}

    expression = {
        "$relationships": [{"$type": "RELATES_TO", "ok": True}, {"$type": "RELATES_TO", "ok": {"$not": True}}]
    }
    normalized = operators_builder.normalize_expressions(expression)
    assert normalized == {
        "$relationships": [
            {"$type": "RELATES_TO", "ok": {"$eq": True}},
            {"$type": "RELATES_TO", "ok": {"$not": {"$eq": True}}},
        ]
    }


def test_remove_invalid_expressions(operators_builder: Operators):
    # Test removing empty nested objects
    expressions = {"$and": [{"$or": []}, {"name": "John"}]}
    operators_builder.remove_invalid_expressions(expressions)
    assert not expressions

    # Test removing nested objects with invalid keys
    expressions = {"$and": [{"$or": [{"age": {"$gt": 30}}, {"age": {"gt": 20}}]}, {"name": {"$eq": "John"}}]}
    operators_builder.remove_invalid_expressions(expressions)
    assert expressions == {"$and": [{"$or": [{"age": {"$gt": 30}}]}, {"name": {"$eq": "John"}}]}

    # Test removing empty lists
    expressions = {"$and": [{"$or": [{"age": {"$gt": 30}}, []]}, {"name": {"$eq": "John"}}]}
    operators_builder.remove_invalid_expressions(expressions)
    assert expressions == {"$and": [{"$or": [{"age": {"$gt": 30}}]}, {"name": {"$eq": "John"}}]}


def test_invalid_filter_returns_none(operators_builder: Operators):
    query_string = operators_builder.build_operators("not a filter")  # type: ignore
    assert query_string is None
    assert operators_builder.parameters == {}


def test_omit_invalid_operators(operators_builder: Operators):
    query_string = operators_builder.build_operators({"a": {"$doesnotexist": "a", "$eq": "b"}})
    assert query_string == "n.a = $_n_0"
    assert operators_builder.parameters == {"_n_0": "b"}
