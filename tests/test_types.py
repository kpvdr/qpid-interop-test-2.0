"""Tests for AMQP type definitions."""

from qit.types import AmqpPrimitiveTypes


def test_all_types_defined() -> None:
    """Verify all AMQP primitive types are defined."""
    all_types = AmqpPrimitiveTypes.get_all_types()

    expected_types = {
        "null",
        "boolean",
        "ubyte",
        "ushort",
        "uint",
        "ulong",
        "byte",
        "short",
        "int",
        "long",
        "float",
        "double",
        "char",
        "timestamp",
        "uuid",
        "binary",
        "string",
        "symbol",
    }

    assert set(all_types.keys()) == expected_types


def test_type_values_not_empty() -> None:
    """Verify each type has test values defined."""
    all_types = AmqpPrimitiveTypes.get_all_types()

    for type_name, type_def in all_types.items():
        assert "values" in type_def, f"Type {type_name} missing values"
        assert len(type_def["values"]) > 0, f"Type {type_name} has no test values"


def test_get_type_values() -> None:
    """Test retrieving values for specific types."""
    uint_values = AmqpPrimitiveTypes.get_type_values("uint")
    assert len(uint_values) > 0
    assert 0x00000000 in uint_values
    assert 0xFFFFFFFF in uint_values


def test_boolean_values() -> None:
    """Test boolean type has True and False."""
    values = AmqpPrimitiveTypes.get_type_values("boolean")
    assert True in values
    assert False in values
    assert len(values) == 2


def test_null_value() -> None:
    """Test null type has None value."""
    values = AmqpPrimitiveTypes.get_type_values("null")
    assert len(values) == 1
    assert values[0] is None
