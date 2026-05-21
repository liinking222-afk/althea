#!/bin/bash
# althea_memory_filter.sh - Extract structured events from Althea memory stream
# Usage: cat memories.txt | ./althea_memory_filter.sh [GROWTH|EVO|ALL]

EVENT_TYPE="${1:-ALL}"

while IFS= read -r line; do
  case "$line" in
    *"[GROWTH "*)
      path=$(echo "$line" | sed -n 's/.*\[GROWTH \([^]]*\)\].*/\1/p')
      desc=$(echo "$line" | sed -n 's/.*] \([^—]*\).*/\1/p' | xargs)
      tag=$(echo "$line" | sed -n 's/.*(\([^)]*\)).*/\1/p')
      if [ "$EVENT_TYPE" = "GROWTH" ] || [ "$EVENT_TYPE" = "ALL" ]; then
        echo "GROWTH|$path|$tag|$desc"
      fi
      ;;
    *"[EVO #"*)
      num=$(echo "$line" | sed -n 's/.*#\([0-9]*\).*/\1/p')
      arch=$(echo "$line" | sed -n 's/.*#[0-9]* \([A-Z]*\).*/\1/p')
      ver=$(echo "$line" | sed -n 's/.*\(v[0-9.]*→[0-9.]*\).*/\1/p')
      desc=$(echo "$line" | sed -n 's/.*] \([^—]*\).*/\1/p' | xargs)
      if [ "$EVENT_TYPE" = "EVO" ] || [ "$EVENT_TYPE" = "ALL" ]; then
        echo "EVO|#$num|$arch|$ver|$desc"
      fi
      ;;
  esac
done

# Compose with: cat memories.txt | ./althea_memory_filter.sh GROWTH | cut -d'|' -f3 | sort | uniq -c
# Or: ./althea_memory_filter.sh EVO | grep THOMPSON
# Or: ./althea_memory_filter.sh ALL | awk -F'|' '{print $1}' | sort | uniq -c