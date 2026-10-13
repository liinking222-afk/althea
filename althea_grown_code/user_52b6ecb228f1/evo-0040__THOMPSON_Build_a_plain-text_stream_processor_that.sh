#!/bin/bash
# stream_memory_filter.sh - Composable memory pattern extractor

read_memory_stream() {
  cat "$1" 2>/dev/null || echo "$1"
}

extract_signals() {
  grep -oE '\[GROWTH [^]]+\]|\[EVO [^]]+\]|\[SYSTEM-MAP\]' | 
  sed 's/\[//g; s/\]//g'
}

frequency_count() {
  awk '{
    for(i=1; i<=NF; i++) {
      if ($i ~ /^\//) words[$i]++
      if ($i == "perception" || $i == "chaos") types[$i]++
    }
  }
  END {
    for (w in words) print words[w], "module", w
    for (t in types) print types[t], "type", t
  }' | sort -rn
}

detect_clusters() {
  awk '$2 == "module" {print $3}' |
  sed 's/.*\///' |
  awk '{
    for(i=1; i<=length($0); i++) {
      c = substr($0, i, 1)
      if (c ~ /[a-z]/) chars[c]++
    }
  }
  END {
    for (ch in chars) if (chars[ch] > 2) print ch
  }' | 
  tr -d '\n' | 
  awk '{print "letter_cluster:", $0}'
}

synthesize() {
  tee >(frequency_count >&2) | detect_clusters
}

main() {
  read_memory_stream "${1:-/dev/stdin}" | 
  extract_signals | 
  synthesize
}

main "$@"