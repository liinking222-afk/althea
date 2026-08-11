#!/bin/bash
# capability_sifter.sh - UNIX-style capability module analyzer

extract_actions() {
  grep -oE '\b(get|set|create|delete|update|read|write|process|transform|validate|check|find|filter|map|reduce|generate|parse|format|load|save|emit|handle|execute|measure|count|extract|build|compile|inject|resolve|traverse|stabilize|attenuate|modulate|swap|replace|identify|destabilize|introduce)[A-Z][a-zA-Z]*' "$1" 2>/dev/null | sort | uniq
}

count_responsibilities() {
  local file="$1"
  local actions=$(extract_actions "$file")
  echo "$actions" | wc -l
}

score_module() {
  local file="$1"
  local resp_count=$(count_responsibilities "$file")
  local lines=$(wc -l < "$file" 2>/dev/null || echo 0)
  local score=0
  
  [ "$lines" -gt 0 ] && score=$(awk "BEGIN {printf \"%.2f\", $resp_count / ($lines / 10.0)}")
  
  echo -e "$score\t$resp_count\t$lines\t$file"
}

# Main pipeline
find "${1:-.}" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" \) -print0 2>/dev/null |
  while IFS= read -r -d '' file; do
    score_module "$file"
  done |
  sort -rn |
  awk 'BEGIN {print "SCORE\tRESP\tLINES\tMODULE"} {print}'

# Stream mode: tail -f module.log | ./capability_sifter.sh -
if [ "$1" = "-" ]; then
  while IFS= read -r line; do
    echo "$line" | extract_actions /dev/stdin
  done
fi