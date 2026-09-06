#!/bin/bash
# stream_extract.sh - UNIX-philosophy log parser that composes with pipes

extract_field() {
    local pattern="$1"
    local field="$2"
    grep -oP "$pattern" | sed "s/.*$field:\s*\K[^;]*//" | sed 's/[[:space:]]*$//'
}

stream_parse() {
    while IFS= read -r line; do
        # Extract memory type markers
        if echo "$line" | grep -q '\[.*\]'; then
            type=$(echo "$line" | grep -oP '\[\K[^\]]+')
            echo "$type" | tr '[:upper:]' '[:lower:]'
        fi
        
        # Extract concept lists
        if echo "$line" | grep -q 'concepts:'; then
            echo "$line" | grep -oP 'concepts:\s*\K[^·]+' | tr ';' '\n' | sed 's/^[[:space:]]*//'
        fi
        
        # Extract confidence scores
        if echo "$line" | grep -q 'conf'; then
            echo "$line" | grep -oP 'conf\s+\K[0-9.]+' | awk '{print "confidence:" $1}'
        fi
        
        # Extract pattern names
        if echo "$line" | grep -q 'pattern'; then
            echo "$line" | grep -oP "'[^']*pattern[^']*'" | tr -d "'" | awk '{print "pattern:" $0}'
        fi
    done
}

# Composable filters
filter_confidence() {
    local threshold="${1:-0.9}"
    awk -F: -v t="$threshold" '/^confidence:/ && $2 >= t'
}

filter_type() {
    local type="$1"
    grep "^$type$"
}

# Main dispatcher
case "${1:-parse}" in
    parse) stream_parse ;;
    conf) shift; filter_confidence "$@" ;;
    type) shift; filter_type "$@" ;;
    field) shift; extract_field "$@" ;;
    *) stream_parse ;;
esac