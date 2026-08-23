#!/bin/bash
# module_stream.sh - Extract module metadata as line-delimited plain text
# Usage: cat module.py | ./module_stream.sh [--intent|--imports|--functions|--all]

MODE="${1:---all}"

extract_intent() {
  grep -oP '(?<=INTENT:\s).*' | head -1
}

extract_imports() {
  grep -E '^(import|from)\s' | sed 's/^/IMPORT: /'
}

extract_functions() {
  grep -oP '^def\s+\K[a-zA-Z_][a-zA-Z0-9_]*(?=\()' | sed 's/^/FUNC: /'
}

extract_classes() {
  grep -oP '^class\s+\K[a-zA-Z_][a-zA-Z0-9_]*' | sed 's/^/CLASS: /'
}

case "$MODE" in
  --intent)
    extract_intent
    ;;
  --imports)
    extract_imports
    ;;
  --functions)
    extract_functions
    extract_classes
    ;;
  --all)
    echo "=== MODULE STREAM ==="
    extract_intent
    extract_imports
    extract_functions
    extract_classes
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    exit 1
    ;;
esac