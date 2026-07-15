#!/usr/bin/env bash
#
# QIT .NET Proton Shim Wrapper
#
# Wraps the .NET executable to match the expected shim interface
#

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Path to the compiled .NET executable
DOTNET_SHIM="$SCRIPT_DIR/bin/Release/net8.0/qit-shim-dotnet"

# Check if built
if [ ! -f "$DOTNET_SHIM" ]; then
    echo "Error: .NET shim not built. Run: cd $SCRIPT_DIR && dotnet build -c Release" >&2
    exit 1
fi

# Forward all arguments to the .NET executable
exec "$DOTNET_SHIM" "$@"
