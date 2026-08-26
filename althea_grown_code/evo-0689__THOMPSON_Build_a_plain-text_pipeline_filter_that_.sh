#!/usr/bin/env bash
# memory-stream-parser.sh — Extract structured fields from Althea memory logs
# Usage: cat memory.log | ./memory-stream-parser.sh [--type=TYPE] [--field=FIELD]
# Output: TSV with fields: timestamp, type, id, name, category, description

set -euo pipefail

TYPE_FILTER=""
FIELD_SELECT=""

for arg in "$@"; do
  case $arg in
    --type=*) TYPE_FILTER="${arg#*=}" ;;
    --field=*) FIELD_SELECT="${arg#*=}" ;;
  esac
done

while IFS= read -r line; do
  # Match patterns: [TYPE /id] Name (category). Description
  # or [TYPE #num NAME version] Description
  
  if [[ "$line" =~ ^\[([A-Z]+)[[:space:]]+(/?[a-z0-9-]+|#[0-9]+[[:space:]]+[A-Z]+[[:space:]]+[v0-9.→]+)\][[:space:]]*(.*)$ ]]; then
    type="${BASH_REMATCH[1]}"
    id="${BASH_REMATCH[2]}"
    rest="${BASH_REMATCH[3]}"
    
    # Apply type filter
    [[ -n "$TYPE_FILTER" && "$type" != "$TYPE_FILTER" ]] && continue
    
    # Parse name (category). description pattern
    if [[ "$rest" =~ ^([^(]+)[[:space:]]*\(([^)]+)\)\.[[:space:]]*(.*)$ ]]; then
      name="${BASH_REMATCH[1]}"
      category="${BASH_REMATCH[2]}"
      desc="${BASH_REMATCH[3]}"
    else
      name="$rest"
      category=""
      desc=""
    fi
    
    # Clean whitespace
    name=$(echo "$name" | xargs)
    category=$(echo "$category" | xargs)
    desc=$(echo "$desc" | xargs)
    
    # Output TSV
    if [[ -z "$FIELD_SELECT" ]]; then
      printf "%s\t%s\t%s\t%s\t%s\n" "$type" "$id" "$name" "$category" "$desc"
    else
      case "$FIELD_SELECT" in
        type) echo "$type" ;;
        id) echo "$id" ;;
        name) echo "$name" ;;
        category) echo "$category" ;;
        desc) echo "$desc" ;;
      esac
    fi
  fi
done