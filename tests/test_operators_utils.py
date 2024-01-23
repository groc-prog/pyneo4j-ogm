# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from pyneo4j_ogm.queries.operators import Operators
from tests.fixtures.operators_builder import operators_builder


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
