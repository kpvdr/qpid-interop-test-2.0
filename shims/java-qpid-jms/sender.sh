#!/bin/bash
# QIT 2.0 - JMS Sender Shim Wrapper

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR_FILE="${SCRIPT_DIR}/target/qit-jms-shim-2.0.0-jar-with-dependencies.jar"

if [ ! -f "${JAR_FILE}" ]; then
    echo "ERROR: JAR file not found: ${JAR_FILE}" >&2
    echo "Run 'mvn package' in ${SCRIPT_DIR} first" >&2
    exit 1
fi

# Run JMS Sender
exec java -cp "${JAR_FILE}" org.apache.qpid.qit.JmsSender "$@"
