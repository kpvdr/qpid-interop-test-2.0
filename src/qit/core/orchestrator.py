"""
Test orchestration engine.

Coordinates shim execution, message comparison, and result reporting.
"""

from dataclasses import dataclass
from itertools import product
from typing import Any

from qit.core.broker import BrokerManager
from qit.core.comparison import MessageComparator, MessageDiff
from qit.core.shim import Shim


@dataclass
class TestCase:
    """Represents a single interoperability test case."""

    sender_shim: str
    receiver_shim: str
    amqp_type: str
    test_values: list[Any]


@dataclass
class TestResult:
    """Result of a test case execution."""

    test_case: TestCase
    success: bool
    diffs: list[MessageDiff]
    error: str | None = None
    duration_ms: float = 0.0


class Orchestrator:
    """Orchestrates interoperability tests across shims."""

    def __init__(
        self,
        shims: dict[str, Shim],
        broker: BrokerManager | None = None,
    ) -> None:
        self.shims = shims
        self.broker = broker
        self.comparator = MessageComparator()

    def run_test_matrix(
        self,
        amqp_types: dict[str, list[Any]],
        sender_shims: list[str] | None = None,
        receiver_shims: list[str] | None = None,
    ) -> list[TestResult]:
        """
        Run full test matrix: all sender × receiver × type combinations.

        Args:
            amqp_types: Map of type name to list of test values
            sender_shims: List of sender shim names (default: all shims)
            receiver_shims: List of receiver shim names (default: all shims)

        Returns:
            List of test results
        """
        # Default to all available shims
        sender_names = sender_shims or list(self.shims.keys())
        receiver_names = receiver_shims or list(self.shims.keys())

        # Generate test cases
        test_cases: list[TestCase] = []
        for sender, receiver, (type_name, values) in product(
            sender_names,
            receiver_names,
            amqp_types.items(),
        ):
            test_cases.append(
                TestCase(
                    sender_shim=sender,
                    receiver_shim=receiver,
                    amqp_type=type_name,
                    test_values=values,
                )
            )

        print(f"Running {len(test_cases)} test cases...")
        print(f"  Senders: {', '.join(sender_names)}")
        print(f"  Receivers: {', '.join(receiver_names)}")
        print(f"  Types: {', '.join(amqp_types.keys())}")
        print()

        # Run tests
        results: list[TestResult] = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] Testing {test_case.sender_shim} → {test_case.receiver_shim} "
                  f"({test_case.amqp_type})...", end=" ", flush=True)

            result = self.run_test_case(test_case)
            results.append(result)

            if result.success:
                print("✓")
            else:
                print("✗")
                if result.error:
                    print(f"  Error: {result.error}")
                if result.diffs:
                    print(f"  {len(result.diffs)} difference(s) found")

        return results

    def run_test_case(self, test_case: TestCase) -> TestResult:
        """
        Run a single test case.

        Args:
            test_case: Test case to execute

        Returns:
            Test result
        """
        import time

        start_time = time.time()

        try:
            # Get shims
            sender = self.shims.get(test_case.sender_shim)
            receiver = self.shims.get(test_case.receiver_shim)

            if not sender:
                return TestResult(
                    test_case=test_case,
                    success=False,
                    diffs=[],
                    error=f"Sender shim not found: {test_case.sender_shim}",
                )

            if not receiver:
                return TestResult(
                    test_case=test_case,
                    success=False,
                    diffs=[],
                    error=f"Receiver shim not found: {test_case.receiver_shim}",
                )

            # Ensure broker is available
            if self.broker is None:
                return TestResult(
                    test_case=test_case,
                    success=False,
                    diffs=[],
                    error="No broker configured (use --mode direct for broker-less tests)",
                )

            # Generate unique queue name for this test
            queue_name = f"qit.test.{test_case.amqp_type}.{test_case.sender_shim}.{test_case.receiver_shim}"

            # Send messages
            send_result = sender.send(
                broker_url=self.broker.config.url,
                queue_name=queue_name,
                amqp_type=test_case.amqp_type,
                values=test_case.test_values,
            )

            if not send_result.success:
                return TestResult(
                    test_case=test_case,
                    success=False,
                    diffs=[],
                    error=f"Send failed: {send_result.error}",
                )

            # Receive messages
            recv_result = receiver.receive(
                broker_url=self.broker.config.url,
                queue_name=queue_name,
                count=len(test_case.test_values),
                timeout=5,  # 5 second timeout - messages should arrive quickly
            )

            if not recv_result.success:
                return TestResult(
                    test_case=test_case,
                    success=False,
                    diffs=[],
                    error=f"Receive failed: {recv_result.error}",
                )

            # Compare messages
            diffs = self.comparator.compare_messages(
                send_result.messages,
                recv_result.messages,
            )

            duration_ms = (time.time() - start_time) * 1000

            return TestResult(
                test_case=test_case,
                success=len(diffs) == 0,
                diffs=diffs,
                duration_ms=duration_ms,
            )

        except Exception as e:
            return TestResult(
                test_case=test_case,
                success=False,
                diffs=[],
                error=f"Unexpected error: {e}",
            )

    def generate_report(self, results: list[TestResult]) -> str:
        """Generate a summary report of test results."""
        total = len(results)
        passed = sum(1 for r in results if r.success)
        failed = total - passed

        lines = [
            "=" * 80,
            "Test Results Summary",
            "=" * 80,
            f"Total:  {total}",
            f"Passed: {passed} ({100 * passed / total:.1f}%)" if total > 0 else "Passed: 0",
            f"Failed: {failed}",
            "",
        ]

        if failed > 0:
            lines.append("Failed Tests:")
            lines.append("-" * 80)
            for result in results:
                if not result.success:
                    tc = result.test_case
                    lines.append(f"  {tc.sender_shim} → {tc.receiver_shim} ({tc.amqp_type})")
                    if result.error:
                        lines.append(f"    Error: {result.error}")
                    if result.diffs:
                        for diff in result.diffs[:3]:  # Show first 3 diffs
                            lines.append(f"    {diff.message}")
                        if len(result.diffs) > 3:
                            lines.append(f"    ... and {len(result.diffs) - 3} more")
                    lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def generate_junit_xml(self, results: list[TestResult], output_path: str) -> None:
        """
        Generate JUnit XML report for CI/CD integration.

        Args:
            results: Test results to report
            output_path: Path to write XML file
        """
        from pathlib import Path
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        total = len(results)
        passed = sum(1 for r in results if r.success)
        failed = total - passed
        total_time_sec = sum(r.duration_ms for r in results) / 1000

        # Create root testsuite element
        testsuite = Element(
            "testsuite",
            name="QIT AMQP Interoperability Tests",
            tests=str(total),
            failures=str(failed),
            errors="0",
            skipped="0",
            time=f"{total_time_sec:.3f}",
        )

        # Add test cases
        for result in results:
            tc = result.test_case
            testcase = SubElement(
                testsuite,
                "testcase",
                classname=f"qit.{tc.sender_shim}.{tc.receiver_shim}",
                name=f"{tc.amqp_type}",
                time=f"{result.duration_ms / 1000:.3f}",
            )

            if not result.success:
                # Add failure element
                failure_msg = result.error if result.error else f"{len(result.diffs)} message difference(s)"
                failure_details = []

                if result.error:
                    failure_details.append(f"Error: {result.error}")

                if result.diffs:
                    failure_details.append(f"\nMessage Differences ({len(result.diffs)} total):")
                    for diff in result.diffs[:10]:  # Include up to 10 diffs
                        failure_details.append(f"  - {diff.message}")
                    if len(result.diffs) > 10:
                        failure_details.append(f"  ... and {len(result.diffs) - 10} more differences")

                failure = SubElement(
                    testcase,
                    "failure",
                    message=failure_msg,
                    type="InteroperabilityFailure",
                )
                failure.text = "\n".join(failure_details)

        # Pretty print and write to file
        xml_str = minidom.parseString(tostring(testsuite, encoding="unicode")).toprettyxml(indent="  ")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
