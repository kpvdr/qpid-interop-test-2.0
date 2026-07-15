#!/bin/bash
# Wrapper script to run C++ Proton shim

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHIM_EXECUTABLE="$SCRIPT_DIR/build/qit-shim-cpp"

if [ ! -f "$SHIM_EXECUTABLE" ]; then
    echo "Error: Shim executable not found. Please build first with:" >&2
    echo "  cd $SCRIPT_DIR && mkdir -p build && cd build && cmake .. && make" >&2
    exit 1
fi

exec "$SHIM_EXECUTABLE" "$@"
