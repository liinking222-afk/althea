#!/bin/bash
# althea_pipe_extract.sh - Extract composable module signatures from evolution logs
# Usage: cat evolution.log | ./althea_pipe_extract.sh [filter_pattern]
# Output: module_name|version|callable_signature

set -euo pipefail

FILTER="${1:-.*}"

while IFS= read -r line; do
    # Extract EVO entries with module names and versions
    if echo "$line" | grep -q '\[EVO #'; then
        # Parse: [EVO #NUM ARCHETYPE vOLD→vNEW] description
        evo_num=$(echo "$line" | sed -n 's/.*\[EVO #\([0-9]*\).*/\1/p')
        archetype=$(echo "$line" | sed -n 's/.*EVO #[0-9]* \([A-Z]*\).*/\1/p')
        version=$(echo "$line" | sed -n 's/.*v\([0-9.]*\)→\([0-9.]*\).*/\2/p')
        desc=$(echo "$line" | sed -n 's/.*→[0-9.]*\] \(.*\) —.*/\1/p')
        
        if [ -n "$archetype" ] && [ -n "$version" ] && echo "$archetype" | grep -qE "$FILTER"; then
            # Generate callable signature from description
            sig=$(echo "$desc" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g' | sed 's/__*/_/g' | sed 's/^_//;s/_$//')
            echo "${archetype}.${sig}|v${version}|${evo_num}"
        fi
    fi
done | sort -t'|' -k3 -n | awk -F'|' '{print $1 "|" $2}'