#!/usr/bin/env bash
# polyglot_input_shim.sh — WALL-style pragmatic glue for Althea's pipeline toolkit

detect_and_parse() {
  local first_line=$(head -n1)
  local rest=$(cat)
  local all_input=$(printf "%s\n%s" "$first_line" "$rest")
  
  # Duck-typing: if it quacks like JSON...
  if echo "$first_line" | grep -qE '^\s*\{.*\}\s*$'; then
    # Single-line JSON object or NDJSON
    echo "$all_input" | while IFS= read -r line; do
      [ -z "$line" ] && continue
      echo "$line" | jq -c '.'
    done
  elif echo "$first_line" | grep -qE '^\s*\['; then
    # JSON array
    echo "$all_input" | jq -c '.[]'
  elif echo "$first_line" | grep -qE '^[^,]+,[^,]+'; then
    # Looks like CSV
    echo "$all_input" | awk -F, 'NR==1{for(i=1;i<=NF;i++)h[i]=$i;next} {printf "{"; for(i=1;i<=NF;i++){gsub(/^[ \t]+|[ \t]+$/,"",$i); printf "\"%s\":\"%s\"",h[i],$i; if(i<NF)printf","} print "}"}'
  elif echo "$first_line" | grep -qE '^[A-Z_]+:'; then
    # Key-value format (EVOLUTION-ID:, DELTA:, etc)
    echo "$all_input" | awk -F: '{gsub(/^[ \t]+|[ \t]+$/,"",$2); printf "{\"key\":\"%s\",\"value\":\"%s\"}\n",$1,$2}'
  else
    # Plain text: emit as line-delimited JSON objects
    echo "$all_input" | awk '{printf "{\"line\":%d,\"text\":\"%s\"}\n",NR,$0}'
  fi
}

# Usage: cat input | ./polyglot_input_shim.sh | jq '.field'
# Or: ./polyglot_input_shim.sh < data.txt | grep pattern
if [ -t 0 ]; then
  echo "Usage: cat input | $0" >&2
  echo "Detects format and emits normalized NDJSON for pipeline composition" >&2
  exit 1
fi

detect_and_parse