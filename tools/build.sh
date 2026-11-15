#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BASE_ROM="EarthBound (USA).sfc"
BUILD_DIR="build"
EXPANDED_BASE="$BUILD_DIR/base_32mbit.sfc"
OUTPUT_ROM="$BUILD_DIR/eb_zero_fault.sfc"
COILSNAKE_BIN=".venv/bin/coilsnake-cli"

if [ ! -f "$COILSNAKE_BIN" ]; then
    echo "Error: CoilSnake virtual environment binary not found at $COILSNAKE_BIN"
    exit 1
fi

if [ ! -f "$BASE_ROM" ]; then
    echo "Error: Base ROM not found at $BASE_ROM"
    exit 1
fi

mkdir -p "$BUILD_DIR"

if [ ! -f "$EXPANDED_BASE" ]; then
    echo "Preparing expanded 32-Mbit intermediate base ROM..."
    cp "$BASE_ROM" "$EXPANDED_BASE"
    "$COILSNAKE_BIN" expand "$EXPANDED_BASE" false
fi

echo "Compiling project to $OUTPUT_ROM..."
"$COILSNAKE_BIN" compile src "$EXPANDED_BASE" "$OUTPUT_ROM"
echo "Build complete: $OUTPUT_ROM ($(stat -c %s "$OUTPUT_ROM") bytes)"
