#!/bin/bash
# memory_stream.sh - UNIX philosophy memory pipeline toolkit

# Extract memories as newline-delimited JSON
memory_extract() {
    local pattern="${1:-.}"
    grep -E "$pattern" "$MEMORY_LOG" 2>/dev/null | \
    jq -c '{ts:.timestamp, type:.type, id:.id, content:.content}'
}

# Filter by event type
memory_filter_type() {
    local type="$1"
    jq -c "select(.type == \"$type\")"
}

# Deduplicate by semantic hash (first 8 chars of content hash)
memory_dedup() {
    awk -F'"' '{
        hash = substr($8, 1, 8)
        if (!seen[hash]++) print
    }'
}

# Count events by type
memory_count() {
    jq -r '.type' | sort | uniq -c | sort -rn
}

# Extract just IDs for further processing
memory_ids() {
    jq -r '.id'
}

# Temporal window filter (last N minutes)
memory_recent() {
    local minutes="${1:-60}"
    local cutoff=$(date -d "$minutes minutes ago" +%s 2>/dev/null || \
                   date -v-${minutes}M +%s)
    jq -c "select(.ts >= $cutoff)"
}

# Compose: deduplicated EVO events from last hour
memory_evo_recent() {
    memory_extract "EVO" | \
    memory_filter_type "evolution" | \
    memory_recent 60 | \
    memory_dedup
}

# Compose: capability synthesis candidates
memory_synthesis_candidates() {
    memory_extract "GROWTH" | \
    memory_filter_type "autonomous_growth" | \
    memory_dedup | \
    jq -c 'select(.content | contains("capability"))'
}

# Main router
case "${1:-extract}" in
    extract) memory_extract "$2" ;;
    filter) memory_filter_type "$2" ;;
    dedup) memory_dedup ;;
    count) memory_count ;;
    ids) memory_ids ;;
    recent) memory_recent "$2" ;;
    evo) memory_evo_recent ;;
    synthesis) memory_synthesis_candidates ;;
    *) memory_extract "." ;;
esac