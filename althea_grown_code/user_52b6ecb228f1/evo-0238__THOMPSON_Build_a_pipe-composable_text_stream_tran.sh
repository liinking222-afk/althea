#!/usr/bin/env bash
# stream-semantic-extract — UNIX-style semantic primitive extractor
# Usage: echo "module output" | stream-semantic-extract | next-tool

set -euo pipefail

# Read entire stdin
input=$(cat)

# Extract verb phrases (actions)
verbs=$(echo "$input" | 
  grep -oE '\b(detect|scan|map|build|extract|validate|measure|transform|accept|emit|compose|query|modify|adjust|chart|spawn|reflect)\b' |
  sort -u |
  tr '\n' ',' |
  sed 's/,$//')

# Extract noun clusters (entities)
nouns=$(echo "$input" | 
  grep -oE '\b[A-Z][a-z]+([A-Z][a-z]+)+\b' |
  sort -u |
  tr '\n' ',' |
  sed 's/,$//')

# Count distinct operations (Thompson simplicity metric)
op_count=$(echo "$verbs" | tr ',' '\n' | grep -v '^$' | wc -l)

# Detect pipeline markers (stdin/stdout/pipe)
is_pipeable=$(echo "$input" | grep -qE '(stdin|stdout|pipe|\|)' && echo "true" || echo "false")

# Emit plain-text key-value stream (greppable, awk-able)
echo "verbs=$verbs"
echo "nouns=$nouns"
echo "operations=$op_count"
echo "pipeable=$is_pipeable"
echo "complexity=$([ "$op_count" -le 3 ] && echo "simple" || echo "complex")"
echo "timestamp=$(date -u +%s)"
echo "---"
cat <<< "$input"