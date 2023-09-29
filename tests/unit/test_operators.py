# pylint: disable=invalid-name, redefined-outer-name, unused-import

from pyneo4j_ogm.queries.operators import Operators
from tests.unit.fixtures.operators import operators_builder


def test_reset_state(operators_builder: Operators):
    setattr(operators_builder, "_parameter_indent", 10)
    operators_builder.parameters = {"foo": "bar"}

    operators_builder.reset_state()

    assert getattr(operators_builder, "_parameter_indent", None) == 0
    assert operators_builder.parameters == {}


def test_build_property_var(operators_builder: Operators):
    setattr(operators_builder, "_property_name", "name")

    assert operators_builder.build_property_var() == "n.name"

    setattr(operators_builder, "_property_var_overwrite", "custom_property")
    assert operators_builder.build_property_var() == "custom_property"


def test_build_param_var(operators_builder: Operators):
    assert operators_builder.build_param_var() == "_n_0"
    assert operators_builder.build_param_var() == "_n_1"
    assert operators_builder.build_param_var() == "_n_2"


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


def test_not_operator(operators_builder: Operators):
    expressions = {"name": {"$eq": "John"}}
    query_string = operators_builder.not_operator(expressions)
    assert query_string == "NOT(n.name = $_n_0)"
    assert operators_builder.parameters == {"_n_0": "John"}

    operators_builder.reset_state()
    expressions = {"age": {"$and": [{"$gt": 18}, {"$lt": 30}]}}
    query_string = operators_builder.not_operator(expressions)
    assert query_string == "NOT((n.age > $_n_0 AND n.age < $_n_1))"
    assert operators_builder.parameters == {"_n_0": 18, "_n_1": 30}

    operators_builder.reset_state()
    expressions = {"age": {"$and": [{"$gt": 18}, {"$lt": 30}]}}
    query_string = operators_builder.not_operator(expressions)
    assert query_string == "NOT((n.age > $_n_0 AND n.age < $_n_1))"
    assert operators_builder.parameters == {"_n_0": 18, "_n_1": 30}


def test_size_operator(operators_builder: Operators):
    setattr(operators_builder, "_property_name", "friends")

    expressions = {"$eq": 2}
    query_string = operators_builder.size_operator(expressions)
    assert query_string == "SIZE(n.friends) = $_n_0"
    assert operators_builder.parameters == {"_n_0": 2}

    operators_builder.reset_state()
    expressions = {"$gte": 2}
    query_string = operators_builder.size_operator(expressions)
    assert query_string == "SIZE(n.friends) >= $_n_0"
    assert operators_builder.parameters == {"_n_0": 2}


def test_exists_operator(operators_builder: Operators):
    setattr(operators_builder, "_property_name", "age")

    query_string = operators_builder.exists_operator(True)
    assert query_string == "n.age IS NOT NULL"

    operators_builder.reset_state()
    query_string = operators_builder.exists_operator(False)
    assert query_string == "n.age IS NULL"


def test_labels_operator(operators_builder: Operators):
    query_string = operators_builder.labels_operator(["A", "B"])
    assert query_string == "ALL(i IN labels(n) WHERE i IN $_n_0)"
    assert operators_builder.parameters == {"_n_0": ["A", "B"]}


def test_type_operator(operators_builder: Operators):
    query_string = operators_builder.type_operator("A")
    assert query_string == "type(n) = $_n_0"
    assert operators_builder.parameters == {"_n_0": "A"}

    operators_builder.reset_state()
    query_string = operators_builder.type_operator(["A", "B"])
    assert query_string == "type(n) IN $_n_0"
    assert operators_builder.parameters == {"_n_0": ["A", "B"]}


def test_id_operator(operators_builder: Operators):
    query_string = operators_builder.id_operator(12)
    assert query_string == "ID(n) = $_n_0"
    assert operators_builder.parameters == {"_n_0": 12}


def test_element_id_operator(operators_builder: Operators):
    query_string = operators_builder.element_id_operator("some-id")
    assert query_string == "elementId(n) = $_n_0"
    assert operators_builder.parameters == {"_n_0": "some-id"}


def test_and_operator(operators_builder: Operators):
    query_string = operators_builder.and_operator(
        [{"name": {"$eq": "John"}}, {"age": {"$gt": 18}}, {"age": {"$lte": 30}}]
    )
    assert query_string == "(n.name = $_n_0 AND n.age > $_n_1 AND n.age <= $_n_2)"
    assert operators_builder.parameters == {"_n_0": "John", "_n_1": 18, "_n_2": 30}


def test_or_operator(operators_builder: Operators):
    query_string = operators_builder.or_operator(
        [{"name": {"$eq": "John"}}, {"age": {"$gt": 18}}, {"age": {"$lte": 30}}]
    )
    assert query_string == "(n.name = $_n_0 OR n.age > $_n_1 OR n.age <= $_n_2)"
    assert operators_builder.parameters == {"_n_0": "John", "_n_1": 18, "_n_2": 30}


def test_xor_operator(operators_builder: Operators):
    query_string = operators_builder.xor_operator(
        [{"name": {"$eq": "John"}}, {"age": {"$gt": 18}}, {"age": {"$lte": 30}}]
    )
    assert query_string == "(n.name = $_n_0 XOR n.age > $_n_1 XOR n.age <= $_n_2)"
    assert operators_builder.parameters == {"_n_0": "John", "_n_1": 18, "_n_2": 30}


def test_patterns_operator(operators_builder: Operators):
    query_string = operators_builder.patterns_operator(
        {
            "$node": {"name": {"$eq": "John"}, "$labels": ["A", "B"]},
            "$direction": "OUTGOING",
            "$exists": True,
        }
    )
    assert (
        query_string
        == "EXISTS {MATCH (n)-[_n_0]->(_n_1) WHERE _n_1.name = $_n_2 AND ALL(i IN labels(_n_1) WHERE i IN $_n_3)}"
    )
    assert operators_builder.parameters == {"_n_2": "John", "_n_3": ["A", "B"]}

    operators_builder.reset_state()
    query_string = operators_builder.patterns_operator(
        {
            "$relationship": {"valid": {"$eq": True}, "$type": "VALIDATION"},
            "$direction": "INCOMING",
            "$exists": False,
        }
    )
    assert query_string == "NOT EXISTS {MATCH (n)<-[_n_0]-(_n_1) WHERE _n_0.valid = $_n_2 AND type(_n_0) = $_n_3}"
    assert operators_builder.parameters == {"_n_2": True, "_n_3": "VALIDATION"}

    operators_builder.reset_state()
    query_string = operators_builder.patterns_operator(
        {
            "$node": {"name": {"$eq": "John"}, "$labels": ["A", "B"]},
            "$relationship": {"valid": {"$eq": True}, "$type": "VALIDATION"},
            "$direction": "BOTH",
            "$exists": False,
        }
    )
    assert (
        query_string
        == "NOT EXISTS {MATCH (n)-[_n_0]-(_n_1) WHERE _n_1.name = $_n_2 AND ALL(i IN labels(_n_1) WHERE i IN $_n_3) AND _n_0.valid = $_n_4 AND type(_n_0) = $_n_5}"  # pylint: disable=line-too-long
    )
    assert operators_builder.parameters == {"_n_2": "John", "_n_3": ["A", "B"], "_n_4": True, "_n_5": "VALIDATION"}

    operators_builder.reset_state()
    query_string = operators_builder.patterns_operator(
        {
            "$direction": "INCOMING",
            "$exists": False,
        }
    )
    assert query_string == "NOT EXISTS {MATCH (n)<-[_n_0]-(_n_1)}"
    assert operators_builder.parameters == {}


def test_build_basic_operators(operators_builder: Operators):
    query_string = operators_builder.build_operators(
        {
            "a": {"$eq": "John"},
            "b": {"$neq": 1},
        }
    )
    assert query_string == "n.a = $_n_0 AND n.b <> $_n_1"
    assert operators_builder.parameters == {"_n_0": "John", "_n_1": 1}


def test_build_numeric_operators(operators_builder: Operators):
    query_string = operators_builder.build_operators(
        {
            "a": {"$gt": 1},
            "b": {"$gte": 1},
            "c": {"$lt": 1},
            "d": {"$lte": 1},
        }
    )
    assert query_string == "n.a > $_n_0 AND n.b >= $_n_1 AND n.c < $_n_2 AND n.d <= $_n_3"
    assert operators_builder.parameters == {"_n_0": 1, "_n_1": 1, "_n_2": 1, "_n_3": 1}


def test_build_string_operators(operators_builder: Operators):
    query_string = operators_builder.build_operators(
        {
            "a": {"$icontains": "a"},
            "b": {"$contains": "b"},
            "c": {"$istartsWith": "c"},
            "d": {"$startsWith": "d"},
            "e": {"$iendsWith": "e"},
            "f": {"$endsWith": "f"},
            "g": {"$regex": "\\bg\\w*"},
        }
    )
    assert (
        query_string
        == "toLower(n.a) CONTAINS toLower($_n_0) AND n.b CONTAINS $_n_1 AND toLower(n.c) STARTS WITH toLower($_n_2) AND n.d STARTS WITH $_n_3 AND toLower(n.e) ENDS WITH toLower($_n_4) AND n.f ENDS WITH $_n_5 AND n.g =~ $_n_6"  # pylint: disable=line-too-long
    )
    assert operators_builder.parameters == {
        "_n_0": "a",
        "_n_1": "b",
        "_n_2": "c",
        "_n_3": "d",
        "_n_4": "e",
        "_n_5": "f",
        "_n_6": "\\bg\\w*",
    }


def test_build_list_operators(operators_builder: Operators):
    query_string = operators_builder.build_operators(
        {"a": {"$in": [1, 2]}, "b": {"$nin": ["a", "b"]}, "c": {"$all": [1, 2]}}
    )
    assert (
        query_string
        == "ANY(i IN n.a WHERE i IN $_n_0) AND NONE(i IN n.b WHERE i IN $_n_1) AND ALL(i IN n.c WHERE i IN $_n_2)"
    )
    assert operators_builder.parameters == {
        "_n_0": [1, 2],
        "_n_1": ["a", "b"],
        "_n_2": [1, 2],
    }


def test_build_size_operators(operators_builder: Operators):
    query_string = operators_builder.build_operators(
        {
            "a": {"$size": {"$eq": 1}},
            "b": {"$size": {"$gt": 2}},
            "c": {"$size": {"$gte": 3}},
            "d": {"$size": {"$lt": 4}},
            "e": {"$size": {"$lte": 5}},
        }
    )
    assert (
        query_string
        == "SIZE(n.a) = $_n_0 AND SIZE(n.b) > $_n_1 AND SIZE(n.c) >= $_n_2 AND SIZE(n.d) < $_n_3 AND SIZE(n.e) <= $_n_4"
    )
    assert operators_builder.parameters == {
        "_n_0": 1,
        "_n_1": 2,
        "_n_2": 3,
        "_n_3": 4,
        "_n_4": 5,
    }


def test_build_logical_operators(operators_builder: Operators):
    operators_builder.reset_state()
    query_string = operators_builder.build_operators(
        {
            "a": {"$or": [{"$eq": 1}, {"$eq": 2}]},
            "b": {"$and": [{"$eq": 1}, {"$eq": 2}]},
            "c": {"$xor": [{"$eq": 1}, {"$eq": 2}]},
            "d": {"$not": {"$eq": 1}},
        }
    )
    assert (
        query_string
        == "(n.a = $_n_0 OR n.a = $_n_1) AND (n.b = $_n_2 AND n.b = $_n_3) AND (n.c = $_n_4 XOR n.c = $_n_5) AND NOT(n.d = $_n_6)"
    )
    assert operators_builder.parameters == {
        "_n_0": 1,
        "_n_1": 2,
        "_n_2": 1,
        "_n_3": 2,
        "_n_4": 1,
        "_n_5": 2,
        "_n_6": 1,
    }


def test_build_neo4j_operators(operators_builder: Operators):
    operators_builder.reset_state()
    query_string = operators_builder.build_operators(
        {
            "$id": 12,
            "$elementId": "some-id",
            "a": {"$exists": True},
            "b": {"$exists": False},
        }
    )
    assert query_string == "ID(n) = $_n_0 AND elementId(n) = $_n_1 AND n.a IS NOT NULL AND n.b IS NULL"
    assert operators_builder.parameters == {
        "_n_0": 12,
        "_n_1": "some-id",
    }


def test_build_combined_operators(operators_builder: Operators):
    query_string = operators_builder.build_operators(
        {
            "a": {"$eq": "John"},
            "b": {"$and": [{"$gt": 18}, {"$lt": 30}]},
            "$patterns": [
                {
                    "$node": {"name": {"$eq": "John"}, "$labels": ["A", "B"]},
                    "$direction": "OUTGOING",
                    "$exists": True,
                }
            ],
        }
    )
    assert (
        query_string
        == "n.a = $_n_0 AND (n.b > $_n_1 AND n.b < $_n_2) AND EXISTS {MATCH (n)-[_n_3]->(_n_4) WHERE _n_4.name = $_n_5 AND ALL(i IN labels(_n_4) WHERE i IN $_n_6)}"  # pylint: disable=line-too-long
    )
    assert operators_builder.parameters == {"_n_0": "John", "_n_1": 18, "_n_2": 30, "_n_5": "John", "_n_6": ["A", "B"]}


def test_invalid_filter_returns_none(operators_builder: Operators):
    query_string = operators_builder.build_operators("not a filter")  # type: ignore
    assert query_string is None
    assert operators_builder.parameters == {}


def test_omit_invalid_operators(operators_builder: Operators):
    query_string = operators_builder.build_operators({"a": {"$doesnotexist": "a", "$eq": "b"}})
    assert query_string == "n.a = $_n_0"
    assert operators_builder.parameters == {"_n_0": "b"}
