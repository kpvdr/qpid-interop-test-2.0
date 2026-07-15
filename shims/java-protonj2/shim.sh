#!/usr/bin/env bash
#
# QIT ProtonJ2 Shim Wrapper
#

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to the JAR file
JAR_FILE="$SCRIPT_DIR/target/qit-shim-protonj2.jar"

# Check if built
if [ ! -f "$JAR_FILE" ]; then
    echo "Error: Java shim not built. Run: cd $SCRIPT_DIR && mvn clean package" >&2
    exit 1
fi

# Forward all arguments to java, suppressing warnings
exec java -jar "$JAR_FILE" "$@" 2> >(grep -v "WARNING\|SLF4J" >&2)
