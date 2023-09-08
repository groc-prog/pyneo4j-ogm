# pylint: disable=invalid-name, redefined-outer-name, unused-import

from pyneo4j_ogm.queries.operators import Operators
from tests.unit.fixtures.operators import operators


def test_reset_state(operators: Operators):
    setattr(operators, "_parameter_indent", 10)
    operators.parameters = {"foo": "bar"}

    operators.reset_state()

    assert getattr(operators, "_parameter_indent", None) == 0
    assert operators.parameters == {}


def test_build_property_var(operators: Operators):
    operators.ref = "n"
    setattr(operators, "_property_name", "name")

    assert operators.build_property_var() == "n.name"

    setattr(operators, "_property_var_overwrite", "custom_property")
    assert operators.build_property_var() == "custom_property"


def test_build_param_var(operators: Operators):
    assert operators.build_param_var() == "_n_0"
    assert operators.build_param_var() == "_n_1"
    assert operators.build_param_var() == "_n_2"


def test_normalize_expressions(operators: Operators):
    # Test if key-value pairs without operators are converted to $eq
    expression = {"name": "John"}
    normalized = operators.normalize_expressions(expression)
    assert normalized == {"name": {"$eq": "John"}}

    # Test if `$not` and `$size` operators without a nested operator
    # are converted to `$eq`
    expression = {"name": {"$not": "John"}}
    normalized = operators.normalize_expressions(expression)
    assert normalized == {"name": {"$not": {"$eq": "John"}}}

    expression = {"friends": {"$size": 2}}
    normalized = operators.normalize_expressions(expression)
    assert normalized == {"friends": {"$size": {"$eq": 2}}}

    # Test if multiple defined operators get combined into a single `$and` operator
    # and multiple operators on different keys stay the same
    expression = {"name": {"$neq": "John", "$icontains": "doe"}}
    normalized = operators.normalize_expressions(expression)
    assert normalized == {"name": {"$and": [{"$neq": "John"}, {"$icontains": "doe"}]}}

    expression = {"name": "John", "age": {"$gt": 18}}
    normalized = operators.normalize_expressions(expression)
    assert normalized == {"name": {"$eq": "John"}, "age": {"$gt": 18}}

    # Test if nested operators get normalized
    expression = {"$or": [{"name": "John"}, {"name": "Jane"}]}
    normalized = operators.normalize_expressions(expression)
    assert normalized == {"$or": [{"name": {"$eq": "John"}}, {"name": {"$eq": "Jane"}}]}

    # Test pattern expressions for `$nodes` and `$relationship` operators
    expression = {"$patterns": [{"$node": {"name": "John"}}, {"$relationship": {"name": "Jane"}}]}
    normalized = operators.normalize_expressions(expression)
    assert normalized == {
        "$patterns": [{"$node": {"name": {"$eq": "John"}}}, {"$relationship": {"name": {"$eq": "Jane"}}}]
    }

    # Test normalizations for `$node` and `$relationships` operators
    expression = {"$node": {"name": "Jane", "age": {"$lte": 12}}}
    normalized = operators.normalize_expressions(expression)
    assert normalized == {"$node": {"name": {"$eq": "Jane"}, "age": {"$lte": 12}}}

    expression = {
        "$relationships": [{"$type": "RELATES_TO", "ok": True}, {"$type": "RELATES_TO", "ok": {"$not": True}}]
    }
    normalized = operators.normalize_expressions(expression)
    assert normalized == {
        "$relationships": [
            {"$type": "RELATES_TO", "ok": {"$eq": True}},
            {"$type": "RELATES_TO", "ok": {"$not": {"$eq": True}}},
        ]
    }


def test_remove_invalid_expressions(operators: Operators):
    # Test removing empty nested objects
    expressions = {"$and": [{"$or": []}, {"name": "John"}]}
    operators.remove_invalid_expressions(expressions)
    assert not expressions

    # Test removing nested objects with invalid keys
    expressions = {"$and": [{"$or": [{"age": {"$gt": 30}}, {"age": {"gt": 20}}]}, {"name": {"$eq": "John"}}]}
    operators.remove_invalid_expressions(expressions)
    assert expressions == {"$and": [{"$or": [{"age": {"$gt": 30}}]}, {"name": {"$eq": "John"}}]}

    # Test removing empty lists
    expressions = {"$and": [{"$or": [{"age": {"$gt": 30}}, []]}, {"name": {"$eq": "John"}}]}
    operators.remove_invalid_expressions(expressions)
    assert expressions == {"$and": [{"$or": [{"age": {"$gt": 30}}]}, {"name": {"$eq": "John"}}]}


def test_not_operator(operators: Operators):
    expressions = {"name": {"$eq": "John"}}
    query_string = operators.not_operator(expressions)
    assert query_string == "NOT(n.name = $_n_0)"
    assert operators.parameters == {"_n_0": "John"}

    operators.reset_state()
    expressions = {"age": {"$and": [{"$gt": 18}, {"$lt": 30}]}}
    query_string = operators.not_operator(expressions)
    assert query_string == "NOT((n.age > $_n_0 AND n.age < $_n_1))"
    assert operators.parameters == {"_n_0": 18, "_n_1": 30}

    operators.reset_state()
    expressions = {"age": {"$and": [{"$gt": 18}, {"$lt": 30}]}}
    query_string = operators.not_operator(expressions)
    assert query_string == "NOT((n.age > $_n_0 AND n.age < $_n_1))"
    assert operators.parameters == {"_n_0": 18, "_n_1": 30}


def test_size_operator(operators: Operators):
    operators.ref = "n"
    setattr(operators, "_property_name", "friends")

    expressions = {"$eq": 2}
    query_string = operators.size_operator(expressions)
    assert query_string == "SIZE(n.friends) = $_n_0"
    assert operators.parameters == {"_n_0": 2}

    operators.reset_state()
    expressions = {"$gte": 2}
    query_string = operators.size_operator(expressions)
    assert query_string == "SIZE(n.friends) >= $_n_0"
    assert operators.parameters == {"_n_0": 2}


def test_exists_operator(operators: Operators):
    operators.ref = "n"
    setattr(operators, "_property_name", "age")

    query_string = operators.exists_operator(True)
    assert query_string == "n.age IS NOT NULL"

    operators.reset_state()
    query_string = operators.exists_operator(False)
    assert query_string == "n.age IS NULL"


def test_labels_operator(operators: Operators):
    operators.ref = "n"

    query_string = operators.labels_operator(["A", "B"])
    assert query_string == "ALL(i IN labels(n) WHERE i IN $_n_0)"
    assert operators.parameters == {"_n_0": ["A", "B"]}


def test_type_operator(operators: Operators):
    operators.ref = "n"

    query_string = operators.type_operator("A")
    assert query_string == "type(n) = $_n_0"
    assert operators.parameters == {"_n_0": "A"}

    operators.reset_state()
    query_string = operators.type_operator(["A", "B"])
    assert query_string == "type(n) IN $_n_0"
    assert operators.parameters == {"_n_0": ["A", "B"]}


def test_id_operator(operators: Operators):
    operators.ref = "n"

    query_string = operators.id_operator(12)
    assert query_string == "ID(n) = $_n_0"
    assert operators.parameters == {"_n_0": 12}


def test_element_id_operator(operators: Operators):
    operators.ref = "n"

    query_string = operators.element_id_operator("some-id")
    assert query_string == "elementId(n) = $_n_0"
    assert operators.parameters == {"_n_0": "some-id"}
