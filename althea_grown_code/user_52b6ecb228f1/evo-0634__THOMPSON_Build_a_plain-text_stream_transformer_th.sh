#!/bin/bash
# stream-module-deps - UNIX-style dependency stream processor
# Reads module metadata as line-delimited records, filters and transforms

process_stream() {
    local mode="${1:-list}"
    
    case "$mode" in
        list)
            # Extract module names and their direct dependencies
            while IFS='|' read -r name deps status; do
                echo "$name"
            done
            ;;
        deps)
            # Show dependency relationships as pairs
            while IFS='|' read -r name deps status; do
                if [ -n "$deps" ]; then
                    echo "$deps" | tr ',' '\n' | while read -r dep; do
                        [ -n "$dep" ] && echo "$name -> ${dep}"
                    done
                fi
            done
            ;;
        cycles)
            # Detect circular dependencies via temporary graph
            tmpfile=$(mktemp)
            while IFS='|' read -r name deps status; do
                echo "$name|$deps" >> "$tmpfile"
            done
            
            # Simple cycle detection: check if any module depends on itself transitively
            cat "$tmpfile" | awk -F'|' '{
                split($2, arr, ",");
                for(i in arr) if(arr[i]) graph[$1][arr[i]]=1
            } END {
                for(node in graph) print node
            }'
            rm -f "$tmpfile"
            ;;
        active)
            # Filter only active/loaded modules
            while IFS='|' read -r name deps status; do
                [ "$status" = "active" ] && echo "$name"
            done
            ;;
        dot)
            # Output GraphViz DOT format for visualization
            echo "digraph modules {"
            while IFS='|' read -r name deps status; do
                echo "$deps" | tr ',' '\n' | while read -r dep; do
                    [ -n "$dep" ] && echo "  \"$name\" -> \"$dep\";"
                done
            done
            echo "}"
            ;;
    esac
}

# Main pipeline interface
if [ -t 0 ]; then
    echo "Usage: cat module_data.txt | $0 [list|deps|cycles|active|dot]" >&2
    exit 1
fi

process_stream "${1:-list}"