#!/usr/bin/env bash
# module_stream_tap.sh - UNIX-philosophy cognitive pipeline inspector

set -euo pipefail

PIPE_DIR="${ALTHEA_PIPE_DIR:-/tmp/althea/pipes}"
mkdir -p "$PIPE_DIR"

# Create named pipes for module output streaming
init_taps() {
    local module_name="$1"
    local tap_pipe="$PIPE_DIR/${module_name}.tap"
    [[ -p "$tap_pipe" ]] || mkfifo "$tap_pipe"
    echo "$tap_pipe"
}

# Stream filter: extract only state transitions
filter_transitions() {
    grep -E '^\[STATE|^\[DELTA|^TRANSITION:' | \
    sed 's/^/[TRANS] /'
}

# Stream filter: extract metrics
filter_metrics() {
    grep -E '^[0-9]+\.[0-9]+|coherence|integrity|depth' | \
    awk '{print "[METRIC]", $0}'
}

# Stream filter: extract errors/warnings
filter_alerts() {
    grep -iE 'error|warn|fail|except' | \
    sed 's/^/[ALERT] /' | \
    tee -a "$PIPE_DIR/alerts.log"
}

# Compose filters into pipeline
tap_module() {
    local module="$1"
    local tap=$(init_taps "$module")
    
    # Fork stream to multiple consumers
    tail -f "$tap" | tee \
        >(filter_transitions >> "$PIPE_DIR/transitions.stream") \
        >(filter_metrics >> "$PIPE_DIR/metrics.stream") \
        >(filter_alerts >> "$PIPE_DIR/alerts.stream") \
        > /dev/null &
    
    echo $! > "$PIPE_DIR/${module}.tap.pid"
}

# CLI interface
case "${1:-}" in
    init)   init_taps "$2" ;;
    tap)    tap_module "$2" ;;
    watch)  tail -f "$PIPE_DIR/${2:-transitions}.stream" ;;
    cat)    cat "$PIPE_DIR/${2}.tap" ;;
    clean)  rm -rf "$PIPE_DIR"/* ;;
    *)      echo "Usage: $0 {init|tap|watch|cat|clean} [module_name]" >&2; exit 1 ;;
esac