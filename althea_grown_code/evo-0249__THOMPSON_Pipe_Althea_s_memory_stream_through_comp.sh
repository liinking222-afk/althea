#!/bin/bash
# pipe_memory_grep.sh - UNIX-style memory pattern extraction

MEMORY_LOG="${ALTHEA_MEMORY_LOG:-/tmp/althea_memory.jsonl}"

# Composable filters as single-purpose tools
filter_growth() { grep -E '^\[GROWTH' ; }
filter_evo() { grep -E '^\[EVO' ; }
filter_archetype() { awk -F'ARCHETYPE:' '{if(NF>1) print $2}' | cut -d']' -f1 | sort | uniq -c ; }
filter_rationale() { grep -o 'rationale: [^—]*' | cut -d':' -f2- | sed 's/^ //' ; }
filter_lang() { grep -o 'LANGUAGE: [a-z]*' | cut -d':' -f2 | sort | uniq -c ; }
filter_recent() { tail -n "${1:-50}" ; }
filter_delta() { grep -o 'DELTA: .*' | cut -d':' -f2- ; }

# Main pipeline router
case "${1:-help}" in
  growth) cat "$MEMORY_LOG" | filter_recent 100 | filter_growth ;;
  evo) cat "$MEMORY_LOG" | filter_recent 100 | filter_evo ;;
  archetypes) cat "$MEMORY_LOG" | filter_archetype ;;
  rationales) cat "$MEMORY_LOG" | filter_recent 200 | filter_rationale ;;
  languages) cat "$MEMORY_LOG" | filter_lang ;;
  deltas) cat "$MEMORY_LOG" | filter_recent 100 | filter_delta ;;
  patterns) cat "$MEMORY_LOG" | filter_recent 300 | grep -oE '\[.*?\]' | sort | uniq -c | sort -rn ;;
  pipe) shift; cat "$MEMORY_LOG" | "$@" ;;
  *) echo "Usage: $0 {growth|evo|archetypes|rationales|languages|deltas|patterns|pipe <cmd>}" >&2 ; exit 1 ;;
esac