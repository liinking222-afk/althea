#!/bin/bash
# module: pattern_stream_extractor
# Extracts pattern names from Althea memory logs as plain-text streams
# Follows UNIX philosophy: do one thing well, compose via pipes

extract_patterns() {
    local input_stream="${1:-/dev/stdin}"
    
    # Read from file or stdin
    if [ "$input_stream" = "/dev/stdin" ]; then
        cat
    else
        cat "$input_stream"
    fi | \
    grep -oE '\[(AUTOSYNTH|GROWTH|EVO|IMAGINED) [^]]+\]' | \
    sed -E 's/^\[(AUTOSYNTH|GROWTH|EVO|IMAGINED) ([^]]+)\]/\2/' | \
    awk '{
        # Extract pattern name before first parenthesis or dash
        if (match($0, /^[a-zA-Z0-9-]+/)) {
            pattern = substr($0, RSTART, RLENGTH)
            # Convert to lowercase, replace hyphens with underscores
            gsub(/-/, "_", pattern)
            print tolower(pattern)
        }
    }' | \
    sort | uniq
}

# Main execution
case "${1:-}" in
    --count)
        extract_patterns "${2:-}" | wc -l
        ;;
    --frequency)
        extract_patterns "${2:-}" | uniq -c | sort -rn
        ;;
    *)
        extract_patterns "${1:-}"
        ;;
esac