#!/usr/bin/env bash
# autosynth-extract.sh - Extract AUTOSYNTH patterns as TSV stream
# Usage: cat memory.log | autosynth-extract.sh | sort | uniq -c | sort -rn

set -euo pipefail

# Read stdin line by line, extract AUTOSYNTH patterns, emit TSV
while IFS= read -r line; do
    # Match [AUTOSYNTH /path] Pattern (category). Description
    if echo "$line" | grep -q '^\[AUTOSYNTH '; then
        # Extract path
        path=$(echo "$line" | sed -n 's/.*\[AUTOSYNTH \([^]]*\)\].*/\1/p')
        
        # Extract pattern name (first word after ']')
        pattern=$(echo "$line" | sed -n 's/.*\] \([^ ]*\).*/\1/p')
        
        # Extract category (text in parentheses)
        category=$(echo "$line" | sed -n 's/.*(\([^)]*\)).*/\1/p')
        
        # Emit TSV: path, pattern, category
        if [ -n "$path" ] && [ -n "$pattern" ]; then
            printf "%s\t%s\t%s\n" "$path" "$pattern" "${category:-unknown}"
        fi
    fi
done

# Example pipeline usage (commented):
# cat memory.log | ./autosynth-extract.sh | cut -f2 | sort | uniq -c | sort -rn
# cat memory.log | ./autosynth-extract.sh | awk -F'\t' '{print $3}' | sort | uniq -c
# cat memory.log | ./autosynth-extract.sh | grep -i "linguistic" | wc -l