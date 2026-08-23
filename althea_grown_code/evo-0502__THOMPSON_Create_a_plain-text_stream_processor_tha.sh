#!/bin/bash
# module_stream.sh - UNIX-style module event stream processor

PIPE="${ALTHEA_PIPE:-/tmp/althea_stream}"
[ ! -p "$PIPE" ] && mkfifo "$PIPE"

stream_events() {
  while IFS= read -r line; do
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$timestamp|$line"
  done
}

filter_type() {
  local type="$1"
  grep "^[^|]*|$type|"
}

filter_pattern() {
  local pattern="$1"
  grep "$pattern"
}

count_events() {
  awk -F'|' '{count[$2]++} END {for (type in count) print type, count[type]}'
}

recent() {
  local n="${1:-10}"
  tail -n "$n"
}

emit() {
  local type="$1"
  local module="$2"
  local data="$3"
  echo "$type|$module|$data" >> "$PIPE"
}

case "${1:-stream}" in
  stream)
    cat "$PIPE" | stream_events
    ;;
  filter)
    cat "$PIPE" | stream_events | filter_type "$2"
    ;;
  count)
    cat "$PIPE" | stream_events | count_events
    ;;
  recent)
    cat "$PIPE" | stream_events | recent "$2"
    ;;
  emit)
    emit "$2" "$3" "$4"
    ;;
  watch)
    tail -f "$PIPE" | stream_events | filter_pattern "${2:-.}"
    ;;
  *)
    echo "Usage: $0 {stream|filter|count|recent|emit|watch} [args]"
    exit 1
    ;;
esac