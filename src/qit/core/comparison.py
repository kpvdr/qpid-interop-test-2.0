"""
Message comparison logic for validating interoperability.

Compares sent and received messages, accounting for AMQP type-specific
comparison rules.
"""

from dataclasses import dataclass
from typing import Any

from qit.core.shim import Message


@dataclass
class MessageDiff:
    """Represents a difference between sent and received messages."""

    index: int
    field: str
    expected: Any
    actual: Any
    message: str


class MessageComparator:
    """Compares AMQP messages for equality."""

    def compare_messages(
        self,
        sent: list[Message],
        received: list[Message],
    ) -> list[MessageDiff]:
        """
        Compare sent and received message lists.

        Returns:
            List of differences found (empty if messages match)
        """
        diffs: list[MessageDiff] = []

        # Check counts match
        if len(sent) != len(received):
            diffs.append(
                MessageDiff(
                    index=-1,
                    field="count",
                    expected=len(sent),
                    actual=len(received),
                    message=f"Message count mismatch: expected {len(sent)}, got {len(received)}",
                )
            )
            # Continue comparing available messages
            min_len = min(len(sent), len(received))
        else:
            min_len = len(sent)

        # Compare each message
        for i in range(min_len):
            msg_diffs = self._compare_message(sent[i], received[i])
            diffs.extend(msg_diffs)

        return diffs

    def _compare_message(self, sent: Message, received: Message) -> list[MessageDiff]:
        """Compare a single sent/received message pair."""
        diffs: list[MessageDiff] = []

        # Check type matches
        if sent.amqp_type != received.amqp_type:
            diffs.append(
                MessageDiff(
                    index=sent.index,
                    field="type",
                    expected=sent.amqp_type,
                    actual=received.amqp_type,
                    message=f"Message {sent.index}: type mismatch",
                )
            )

        # Check value matches (type-specific comparison)
        if not self._values_equal(sent.amqp_type, sent.value, received.value):
            diffs.append(
                MessageDiff(
                    index=sent.index,
                    field="value",
                    expected=sent.value,
                    actual=received.value,
                    message=f"Message {sent.index}: value mismatch for type {sent.amqp_type}",
                )
            )

        return diffs

    def _values_equal(self, amqp_type: str, expected: Any, actual: Any) -> bool:
        """
        Type-specific value comparison.

        Handles special cases like:
        - Float/double representation (hex vs decimal)
        - Binary data (hex string vs bytes)
        - String encodings
        """
        # Handle None/null
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False

        # Floating point - compare hex representations for exactness
        if amqp_type in ("float", "double"):
            return self._compare_float(expected, actual)

        # Binary - compare hex representations
        if amqp_type == "binary":
            return self._normalize_hex(expected) == self._normalize_hex(actual)

        # UUID - normalize string representation
        if amqp_type == "uuid":
            return str(expected).lower() == str(actual).lower()

        # String/symbol - direct comparison
        if amqp_type in ("string", "symbol"):
            return str(expected) == str(actual)

        # Boolean
        if amqp_type == "boolean":
            return bool(expected) == bool(actual)

        # Numeric types - direct comparison
        if amqp_type in (
            "ubyte",
            "ushort",
            "uint",
            "ulong",
            "byte",
            "short",
            "int",
            "long",
            "timestamp",
            "char",
        ):
            return int(expected) == int(actual)

        # Fallback to equality
        return expected == actual

    def _compare_float(self, expected: Any, actual: Any) -> bool:
        """Compare floating point values using hex representation."""
        # If both are hex strings, compare directly
        if isinstance(expected, str) and expected.startswith("0x"):
            if isinstance(actual, str) and actual.startswith("0x"):
                return expected.lower() == actual.lower()
            # Convert actual to hex if it's numeric
            return expected.lower() == hex(int(actual)).lower()

        # If both are numeric, compare directly (may have precision issues)
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            return expected == actual

        # Mixed types - try conversion
        try:
            if isinstance(expected, str):
                expected = int(expected, 16)
            if isinstance(actual, str):
                actual = int(actual, 16)
            return expected == actual
        except (ValueError, TypeError):
            return False

    def _normalize_hex(self, value: Any) -> str:
        """Normalize hex string representation."""
        if isinstance(value, bytes):
            return value.hex().lower()
        if isinstance(value, str):
            # Remove any whitespace, 0x prefix, etc.
            return value.replace(" ", "").replace("0x", "").lower()
        return str(value).lower()

    def format_diff_report(self, diffs: list[MessageDiff]) -> str:
        """Format differences as a human-readable report."""
        if not diffs:
            return "✓ All messages match"

        lines = [f"✗ Found {len(diffs)} difference(s):\n"]
        for diff in diffs:
            lines.append(f"  {diff.message}")
            lines.append(f"    Expected: {self._format_value(diff.expected)}")
            lines.append(f"    Actual:   {self._format_value(diff.actual)}")
            lines.append("")

        return "\n".join(lines)

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if isinstance(value, bytes):
            return f"0x{value.hex()}"
        if isinstance(value, str) and len(value) > 50:
            return f"{value[:47]}..."
        return str(value)
