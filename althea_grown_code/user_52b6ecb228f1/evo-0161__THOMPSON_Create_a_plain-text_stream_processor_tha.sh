#!/bin/bash
# stream_modules.sh - UNIX-style module introspection via text streams

set -euo pipefail

MODULE_DIR="${ALTHEA_ROOT:-./modules}"

# Stream all module files as plain text with markers
stream_modules() {
    find "$MODULE_DIR" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
        -exec echo "FILE:{}" \; \
        -exec cat {} \;
}

# Extract function signatures (composable filter)
extract_functions() {
    awk '
        /^FILE:/ { file=$0; next }
        /^(def|function|const.*=>|async function)/ {
            gsub(/^[ \t]+/, "")
            print file "\t" $0
        }
    '
}

# Count lines per file (composable filter)
count_lines() {
    awk '
        /^FILE:/ { if (file) print file "\t" count; file=$2; count=0; next }
        { count++ }
        END { if (file) print file "\t" count }
    '
}

# Extract INTENT/DELTA markers (composable filter)
extract_metadata() {
    awk '
        /^FILE:/ { file=$2; next }
        /INTENT:|DELTA:/ { print file "\t" $0 }
    '
}

# Main router - compose filters via pipes
case "${1:-list}" in
    functions) stream_modules | extract_functions ;;
    lines) stream_modules | count_lines ;;
    meta) stream_modules | extract_metadata ;;
    raw) stream_modules ;;
    *) stream_modules | count_lines | sort -t$'\t' -k2 -rn ;;
esac