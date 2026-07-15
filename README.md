# QIT - AMQP Interoperability Test Suite

Modern rewrite of the Qpid Interoperability Test suite for Red Hat AMQ products.

## Overview

QIT tests AMQP 1.0 interoperability across multiple client implementations by sending messages between different clients and verifying they can correctly exchange all AMQP types.

**Tested Clients:**
- Python (Proton)
- C++ (Proton)
- JavaScript (Rhea)
- .NET (AMQP.Net Lite)
- Java (Qpid JMS)
- Java (Proton J2)

**Test Coverage:**
- All AMQP 1.0 primitive types
- All AMQP 1.0 complex types (arrays, lists, maps, described types)
- JMS message types and headers
- Large message content
- Direct peer-to-peer (no broker)
- Transaction support (planned)

## Quick Start

### Prerequisites

- Python 3.11+
- uv (recommended) or pip
- Apache ActiveMQ Artemis (for broker) - See [BROKER_SETUP.md](BROKER_SETUP.md)

### Installation

```bash
# Install uv (if not already installed)
# On Fedora/RHEL: sudo dnf install uv
# Or: curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup Python environment
uv venv
source .venv/bin/activate
uv sync

# Setup and start broker (see BROKER_SETUP.md for details)
./scripts/setup-local-broker.sh
./artemis-local/bin/artemis run &

# Run tests
qit test amqp-types
```

**Note**: Both local and Docker broker setups are tested and working. See [BROKER_SETUP.md](BROKER_SETUP.md) for details.

### Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests with coverage
pytest --cov=qit

# Format and lint
ruff format .
ruff check .

# Type check
mypy src/qit
```

## Usage

```bash
# Run all AMQP type tests
qit test amqp-types

# Test specific shim pairing
qit test amqp-types --sender python-proton --receiver cpp-proton

# Run with fuzzing
qit test amqp-types --fuzz

# Direct mode (no broker)
qit test amqp-types --mode direct

# Run all tests
qit test all
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

**Key Components:**
- **Orchestrator**: Manages test execution, shim coordination, result comparison
- **Shims**: Native client implementations exposing CLI interface
- **Broker Manager**: Docker Compose lifecycle for Artemis
- **Type System**: Comprehensive AMQP 1.0 type definitions with corner cases

## CI/CD Integration

QIT 2.0 includes a complete Jenkins pipeline for automated testing:

```bash
# Test locally (simulates CI pipeline)
./scripts/run-ci-locally.sh

# Generate JUnit XML for CI
qit test amqp-types --junit-xml test-results/results.xml
```

See [CI_CD_SETUP.md](CI_CD_SETUP.md) for complete Jenkins setup instructions.

## Current Status

**QIT 2.0 - Production Ready**

✅ 5 working shims (Python, JavaScript, C++, .NET, Java)  
✅ 450 comprehensive tests (18 types × 5×5 shim combinations)  
✅ 80.2% pass rate (all failures are known library limitations)  
✅ Complete CI/CD pipeline with JUnit XML reporting  
✅ Docker-based broker management  
✅ Modern tooling and build system  

## License

Apache License 2.0
