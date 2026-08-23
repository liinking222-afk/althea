#!/bin/bash
# event_stream.sh - UNIX-style event processing pipeline for Althea's runtime

FIFO="/tmp/althea_events_$$"
mkfifo "$FIFO" 2>/dev/null || true

process_event() {
  while IFS='|' read -r timestamp module event_type payload; do
    echo "$timestamp|$module|$event_type|$payload"
  done
}

filter_module() {
  local module_pattern="$1"
  grep -E "^[^|]*\|${module_pattern}\|"
}

filter_type() {
  local type_pattern="$1"
  grep -E "^[^|]*\|[^|]*\|${type_pattern}\|"
}

extract_field() {
  local field="$1"
  case "$field" in
    timestamp) cut -d'|' -f1 ;;
    module) cut -d'|' -f2 ;;
    type) cut -d'|' -f3 ;;
    payload) cut -d'|' -f4- ;;
  esac
}

count_events() {
  sort | uniq -c | sort -rn
}

emit() {
  local module="$1"
  local event_type="$2"
  local payload="$3"
  echo "$(date +%s%3N)|${module}|${event_type}|${payload}" >> "$FIFO"
}

tail_stream() {
  cat "$FIFO" | process_event
}

case "${1:-tail}" in
  emit) emit "$2" "$3" "$4" ;;
  tail) tail_stream ;;
  clean) rm -f "$FIFO" ;;
  *) tail_stream ;;
esac