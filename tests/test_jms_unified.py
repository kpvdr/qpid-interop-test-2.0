"""
JMS Interoperability Tests - Unified Client Matrix

Tests JMS message interoperability across all AMQP clients and JMS client.
Structure matches test_types.py (AMQP tests) for consistency.

Test Matrix: N×N (sender × receiver)
- Phase 2b.1: Python + JMS (2×2 = 4 tests)
- Phase 2b.2: + JavaScript (3×3 = 9 tests)
- Phase 2b.3: + C++ (4×4 = 16 tests)
- Phase 2b.4: + .NET (5×5 = 25 tests)
- Phase 2b.5: + Java ProtonJ2 (6×6 = 36 tests)

Message Types: Incremental
- Phase 2b: TextMessage only
- Phase 2c: + BytesMessage, MapMessage, StreamMessage, Message
- Phase 2d: + Headers, Properties
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest


# =============================================================================
# Test Data
# =============================================================================

# TextMessage test values (Phase 2b - initial implementation)
TEXT_MESSAGE_VALUES = [
    "",  # Empty string
    "Hello, world",  # Simple ASCII
    "Charlie's \"peach\"",  # Quotes and apostrophe
    "Unicode: ñ 日本語 🎉",  # Unicode characters
    "The quick brown fox jumped over the lazy dog.",  # Longer text
]

# Future: BytesMessage, MapMessage, StreamMessage, Message
# Future: Headers (JMSCorrelationID, JMSReplyTo, JMSType)
# Future: Properties (boolean, byte, short, int, long, float, double, string)


# =============================================================================
# Client Configurations
# =============================================================================

# Enabled clients for testing (incrementally expand)
ENABLED_CLIENTS = [
    "python-proton",    # Phase 2b.1 ✅
    "jms",              # Phase 2b.1 ✅
    "javascript-rhea",  # Phase 2b.2 ✅
    "cpp-proton",       # Phase 2b.3 ✅
    "dotnet-proton",    # Phase 2b.4 ✅
    # "java-protonj2",    # Phase 2b.5 (future)
]

# Client metadata
CLIENT_INFO = {
    "python-proton": {
        "name": "Python Proton",
        "shim_path": "shims/python-proton/shim.py",
        "jms_mode": True,  # Supports JMS emulation via --jms-mode flag
    },
    "javascript-rhea": {
        "name": "JavaScript Rhea",
        "shim_path": "shims/javascript-rhea/shim.js",
        "jms_mode": True,  # Will support JMS emulation (Phase 2b.2)
    },
    "cpp-proton": {
        "name": "C++ Proton",
        "shim_path": "shims/cpp-proton/build/qit-shim-cpp",
        "jms_mode": True,  # Phase 2b.3 ✅
    },
    "dotnet-proton": {
        "name": ".NET Proton",
        "shim_path": "shims/dotnet-proton/shim.sh",
        "jms_mode": True,  # Phase 2b.4 ✅
    },
    "java-protonj2": {
        "name": "Java ProtonJ2",
        "shim_path": "shims/java-protonj2/sender.sh",
        "jms_mode": True,  # Will support JMS emulation (Phase 2b.5)
    },
    "jms": {
        "name": "Qpid JMS Client",
        "shim_path": "shims/java-qpid-jms/sender.sh",
        "jms_mode": False,  # Native JMS, no emulation needed
    },
}


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def broker_url():
    """Get broker URL from environment or use default."""
    return os.environ.get("QIT_BROKER_URL", "localhost:5672")


@pytest.fixture
def test_queue():
    """Generate unique queue name for test isolation."""
    import random
    import string

    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"qit.test.jms.{suffix}"


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


# =============================================================================
# Shim Runners
# =============================================================================

def run_sender(
    client: str,
    broker_url: str,
    queue: str,
    messages: list[dict[str, Any]],
    project_root: Path,
) -> dict[str, Any]:
    """Run sender shim for any client."""
    client_info = CLIENT_INFO[client]
    shim_path = project_root / client_info["shim_path"]

    if client == "jms":
        # JMS sender (native JMS format)
        cmd = [
            str(shim_path),
            "--broker", broker_url,
            "--queue", queue,
            "--type", "JMS_TEXTMESSAGE_TYPE",
            "--data", json.dumps(messages),
        ]
    elif client == "python-proton":
        # Python sender with JMS emulation
        cmd = [
            "python3", str(shim_path),
            "send",
            "--broker", f"amqp://{broker_url}",
            "--queue", queue,
            "--type", "string",
            "--count", str(len(messages)),
            "--data", json.dumps(messages),
        ]
        if client_info["jms_mode"]:
            cmd.append("--jms-mode")
    elif client == "javascript-rhea":
        # JavaScript sender with JMS emulation
        cmd = [
            "node", str(shim_path),
            "send",
            "--broker", f"amqp://{broker_url}",
            "--queue", queue,
            "--type", "string",
            "--count", str(len(messages)),
            "--data", json.dumps(messages),
        ]
        if client_info["jms_mode"]:
            cmd.append("--jms-mode")
    elif client == "cpp-proton":
        # C++ sender with JMS emulation
        cmd = [
            str(shim_path),
            "send",
            "--broker", f"amqp://{broker_url}",
            "--queue", queue,
            "--type", "string",
            "--count", str(len(messages)),
            "--data", json.dumps(messages),
        ]
        if client_info["jms_mode"]:
            cmd.append("--jms-mode")
    elif client == "dotnet-proton":
        # .NET sender with JMS emulation
        cmd = [
            str(shim_path),
            "send",
            "--broker", f"amqp://{broker_url}",
            "--queue", queue,
            "--type", "string",
            "--count", str(len(messages)),
            "--data", json.dumps(messages),
        ]
        if client_info["jms_mode"]:
            cmd.append("--jms-mode")
    else:
        # Future: Java ProtonJ2
        pytest.skip(f"Sender for {client} not yet implemented")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        pytest.fail(f"{client_info['name']} sender failed: {result.stderr}")

    return json.loads(result.stdout)


def run_receiver(
    client: str,
    broker_url: str,
    queue: str,
    count: int,
    project_root: Path,
    timeout: int = 30,
) -> dict[str, Any]:
    """Run receiver shim for any client."""
    client_info = CLIENT_INFO[client]
    shim_path = project_root / client_info["shim_path"]

    if client == "jms":
        # JMS receiver
        cmd = [
            str(shim_path.parent / "receiver.sh"),
            "--broker", broker_url,
            "--queue", queue,
            "--count", str(count),
            "--timeout", str(timeout),
        ]
    elif client == "python-proton":
        # Python receiver (automatically detects JMS annotation)
        cmd = [
            "python3", str(shim_path),
            "receive",
            "--broker", f"amqp://{broker_url}",
            "--queue", queue,
            "--count", str(count),
            "--timeout", str(timeout),
        ]
    elif client == "javascript-rhea":
        # JavaScript receiver (automatically detects JMS annotation)
        cmd = [
            "node", str(shim_path),
            "receive",
            "--broker", f"amqp://{broker_url}",
            "--queue", queue,
            "--count", str(count),
            "--timeout", str(timeout),
        ]
    elif client == "cpp-proton":
        # C++ receiver (automatically detects JMS annotation)
        cmd = [
            str(shim_path),
            "receive",
            "--broker", f"amqp://{broker_url}",
            "--queue", queue,
            "--count", str(count),
            "--timeout", str(timeout),
        ]
    elif client == "dotnet-proton":
        # .NET receiver (automatically detects JMS annotation)
        cmd = [
            str(shim_path),
            "receive",
            "--broker", f"amqp://{broker_url}",
            "--queue", queue,
            "--count", str(count),
            "--timeout", str(timeout),
        ]
    else:
        # Future: Java ProtonJ2
        pytest.skip(f"Receiver for {client} not yet implemented")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    if result.returncode != 0:
        pytest.fail(f"{client_info['name']} receiver failed: {result.stderr}")

    return json.loads(result.stdout)


# =============================================================================
# Test Helpers
# =============================================================================

def normalize_message_type(msg_type: str) -> str:
    """Normalize message type for comparison (string ↔ text for TextMessage)."""
    if msg_type in ("string", "text"):
        return "text"
    return msg_type


def compare_messages(sent: list[dict], received: list[dict], sender: str, receiver: str) -> None:
    """Compare sent and received messages."""
    if len(sent) != len(received):
        pytest.fail(
            f"{sender}→{receiver}: Message count mismatch - "
            f"sent {len(sent)}, received {len(received)}"
        )

    for i, (s, r) in enumerate(zip(sent, received)):
        # Normalize types
        sent_type = normalize_message_type(s["type"])
        recv_type = normalize_message_type(r["type"])

        assert sent_type == recv_type, (
            f"{sender}→{receiver}: Message {i} type mismatch - "
            f"sent {s['type']}, received {r['type']}"
        )

        assert s["value"] == r["value"], (
            f"{sender}→{receiver}: Message {i} value mismatch - "
            f"sent {repr(s['value'])}, received {repr(r['value'])}"
        )


# =============================================================================
# Test Matrix
# =============================================================================

@pytest.mark.parametrize("sender_client", ENABLED_CLIENTS)
@pytest.mark.parametrize("receiver_client", ENABLED_CLIENTS)
@pytest.mark.parametrize("text_value", TEXT_MESSAGE_VALUES)
def test_jms_textmessage_interop(
    sender_client: str,
    receiver_client: str,
    text_value: str,
    broker_url: str,
    test_queue: str,
    project_root: Path,
):
    """
    Test JMS TextMessage interoperability across all enabled clients.

    This creates a full N×N matrix where N = number of enabled clients.
    Each test sends a message from one client and receives with another.

    Examples:
    - python-proton → python-proton (self-test with JMS annotation)
    - python-proton → jms (AMQP JMS emulation → native JMS)
    - jms → python-proton (native JMS → AMQP JMS detection)
    - jms → jms (JMS baseline, always works)
    """
    # Prepare message
    if sender_client == "jms":
        # JMS expects type="text" for TextMessage
        messages = [{"index": 0, "type": "text", "value": text_value}]
    else:
        # AMQP clients use type="string" (converted to TextMessage via JMS annotation)
        messages = [{"index": 0, "type": "string", "value": text_value}]

    # Send message
    send_result = run_sender(sender_client, broker_url, test_queue, messages, project_root)

    # Receive message
    recv_result = run_receiver(receiver_client, broker_url, test_queue, len(messages), project_root)
    received = recv_result["messages"]

    # Compare
    compare_messages(messages, received, sender_client, receiver_client)


# =============================================================================
# Future: Additional Test Dimensions
# =============================================================================

# Phase 2c: BytesMessage, MapMessage, StreamMessage, Message
# @pytest.mark.parametrize("sender_client", ENABLED_CLIENTS)
# @pytest.mark.parametrize("receiver_client", ENABLED_CLIENTS)
# def test_jms_bytesmessage_interop(sender_client, receiver_client, ...):
#     pass

# Phase 2d: Headers
# @pytest.mark.parametrize("sender_client", ENABLED_CLIENTS)
# @pytest.mark.parametrize("receiver_client", ENABLED_CLIENTS)
# def test_jms_headers_interop(sender_client, receiver_client, ...):
#     pass

# Phase 2e: Properties
# @pytest.mark.parametrize("sender_client", ENABLED_CLIENTS)
# @pytest.mark.parametrize("receiver_client", ENABLED_CLIENTS)
# def test_jms_properties_interop(sender_client, receiver_client, ...):
#     pass
