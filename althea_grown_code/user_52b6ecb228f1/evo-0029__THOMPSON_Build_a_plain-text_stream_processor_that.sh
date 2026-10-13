#!/bin/bash
# memory_stream_pipeline.sh - Unix-philosophy memory processor

set -euo pipefail

# Read memory traces from stdin, one JSON object per line
# Each tool does ONE thing: extract, transform, filter, or annotate

# Extract semantic core (remove metadata noise)
extract_semantic() {
    jq -c '{type, content: .content // .description, timestamp}'
}

# Filter by recency (last N hours, default 24)
filter_recent() {
    local hours="${1:-24}"
    local cutoff=$(date -u -d "$hours hours ago" +%s 2>/dev/null || date -u -v-${hours}H +%s)
    jq -c "select(.timestamp >= $cutoff)"
}

# Tag with concept primitives (simple keyword extraction)
tag_concepts() {
    jq -c '. + {concepts: [.content | scan("\\b[A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*\\b") | ascii_downcase] | unique}'
}

# Rank by semantic density (word diversity ratio)
rank_density() {
    jq -c '. + {density: (.content | split(" ") | unique | length) / ([.content | split(" ") | length, 1] | max)}' |
    sort -t: -k5 -rn
}

# Compose: stdin → extract → filter → tag → rank → stdout
case "${1:-process}" in
    extract) extract_semantic ;;
    filter) shift; filter_recent "$@" ;;
    tag) tag_concepts ;;
    rank) rank_density ;;
    process) extract_semantic | filter_recent | tag_concepts | rank_density ;;
    *) echo "Usage: $0 {extract|filter|tag|rank|process}" >&2; exit 1 ;;
esac