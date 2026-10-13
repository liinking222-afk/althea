#!/bin/bash
# althea_module_stream — UNIX-style module introspection via text streams

MODULES_DIR="${ALTHEA_MODULES:-/tmp/althea/modules}"
mkdir -p "$MODULES_DIR"

# Stream all module metadata as line-delimited records
stream_modules() {
    find "$MODULES_DIR" -type f -name "*.meta" 2>/dev/null | while read -r meta; do
        name=$(basename "$meta" .meta)
        type=$(grep "^type:" "$meta" 2>/dev/null | cut -d: -f2- | xargs)
        status=$(grep "^status:" "$meta" 2>/dev/null | cut -d: -f2- | xargs)
        deps=$(grep "^deps:" "$meta" 2>/dev/null | cut -d: -f2- | xargs)
        echo "$name|$type|$status|$deps"
    done
}

# Filter by type
filter_type() {
    grep -E "\\|${1}\\|"
}

# Filter by status
filter_status() {
    grep -E "\\|[^|]*\\|${1}\\|"
}

# Extract dependency graph edges
deps_graph() {
    while IFS='|' read -r name type status deps; do
        if [ -n "$deps" ]; then
            echo "$deps" | tr ',' '\n' | while read -r dep; do
                [ -n "$dep" ] && echo "$name -> $(echo $dep | xargs)"
            done
        fi
    done
}

# Format as simple table
tabulate() {
    awk -F'|' '{printf "%-30s %-20s %-10s\n", $1, $2, $3}'
}

# Main router
case "${1:-stream}" in
    stream) stream_modules | tabulate ;;
    type) stream_modules | filter_type "$2" | tabulate ;;
    status) stream_modules | filter_status "$2" | tabulate ;;
    deps) stream_modules | deps_graph ;;
    *) stream_modules | tabulate ;;
esac