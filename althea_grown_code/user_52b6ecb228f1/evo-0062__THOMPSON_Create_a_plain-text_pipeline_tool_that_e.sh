#!/usr/bin/env bash
# althea-evo-stream — Extract evolution events as line-delimited records

set -euo pipefail

# Read evolution log from stdin or argument
input="${1:-/dev/stdin}"

# Extract evolution records and emit as pipe-friendly format
grep -E '\[EVO #[0-9]+|GROWTH /' "$input" 2>/dev/null | while IFS= read -r line; do
  if [[ "$line" =~ \[EVO\ \#([0-9]+)\ ([A-Z]+)\ v([0-9.]+)→v([0-9.]+)\]\ (.+)\ —\ (.+) ]]; then
    num="${BASH_REMATCH[1]}"
    archetype="${BASH_REMATCH[2]}"
    from_ver="${BASH_REMATCH[3]}"
    to_ver="${BASH_REMATCH[4]}"
    title="${BASH_REMATCH[5]}"
    desc="${BASH_REMATCH[6]}"
    echo "EVO|${num}|${archetype}|${from_ver}|${to_ver}|${title}|${desc}"
  elif [[ "$line" =~ \[GROWTH\ /([a-z-]+)\]\ (.+)\ \(([a-z]+)\)\.\ (.+)\ —\ (.+) ]]; then
    path="${BASH_REMATCH[1]}"
    title="${BASH_REMATCH[2]}"
    category="${BASH_REMATCH[3]}"
    desc="${BASH_REMATCH[4]}"
    rationale="${BASH_REMATCH[5]}"
    echo "GROWTH|${path}|${category}|${title}|${desc}|${rationale}"
  fi
done

# Usage examples (as comments):
# cat memory.txt | althea-evo-stream
# althea-evo-stream memory.txt | grep THOMPSON
# althea-evo-stream memory.txt | cut -d'|' -f2,6 | column -t -s'|'
# althea-evo-stream memory.txt | awk -F'|' '{print $3}' | sort | uniq -c