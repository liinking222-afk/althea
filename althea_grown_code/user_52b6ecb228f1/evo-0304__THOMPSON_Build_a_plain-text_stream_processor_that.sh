#!/bin/bash
# memgrep - UNIX-style memory pattern processor for Althea
# Reads memories from stdin, applies composable filters, outputs to stdout

filter_by_type() {
    grep -E "^\[$1\]" 
}

extract_tags() {
    sed -n 's/.*\[\([A-Z]*\)[[:space:]].*/\1/p'
}

extract_rationale() {
    sed -n 's/.*—[[:space:]]*rationale:[[:space:]]*\(.*\)/\1/p'
}

extract_versions() {
    grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+→v?[0-9]+\.[0-9]+\.[0-9]+'
}

count_frequency() {
    sort | uniq -c | sort -rn
}

tokenize_concepts() {
    tr '[:upper:]' '[:lower:]' | \
    grep -oE '\b[a-z]{4,}\b' | \
    grep -vE '^(that|this|with|from|build|system)$'
}

measure_complexity() {
    awk '{print length($0), $0}' | sort -rn
}

# Main pipeline router
case "${1:-stream}" in
    evo)     filter_by_type "EVO" ;;
    growth)  filter_by_type "GROWTH" ;;
    tags)    extract_tags | count_frequency ;;
    rationale) extract_rationale ;;
    versions) extract_versions ;;
    concepts) tokenize_concepts | count_frequency | head -20 ;;
    complex) measure_complexity | head -10 ;;
    stream)  cat ;;
    *)       cat ;;
esac