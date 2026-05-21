#!/bin/bash
# memory_verb_pipe.sh - Extract action verbs from memory stream (Thompson style)

# Read memory entries from stdin, one per line
# Expected format: any text containing memory traces with verbs

extract_verbs() {
    # Extract verbs from common memory patterns
    grep -oE '\b(detect|map|extract|count|build|reveal|expose|flag|scan|excavate|erode|generate|define|wipe|click|navigate|write|read|parse|transform|filter|compose|pipe)\w*' \
    | tr '[:upper:]' '[:lower:]' \
    | sed 's/ing$//' \
    | sed 's/ed$//' \
    | sed 's/s$//'
}

count_frequency() {
    sort | uniq -c | sort -rn
}

format_table() {
    awk '{printf "%-20s %5d\n", $2, $1}'
}

# Main pipeline
if [ -t 0 ]; then
    echo "Usage: cat memory.txt | $0" >&2
    echo "Or: $0 < memory.txt" >&2
    exit 1
fi

cat - | extract_verbs | count_frequency | format_table

# Composable: can pipe to grep, head, tail, awk, etc.
# Example: cat memory.txt | ./memory_verb_pipe.sh | head -10
# Example: ./memory_verb_pipe.sh < memory.txt | grep detect