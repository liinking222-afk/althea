#!/bin/bash
# intent_freq - Extract and count intent patterns from Althea logs
# Usage: cat althea.log | intent_freq [--top N]

top_n=10
if [[ "$1" == "--top" && -n "$2" ]]; then
    top_n="$2"
fi

grep -oE '\[GROWTH [^]]+\]|\[EVO #[0-9]+ [^]]+\]|\[AUTOSYNTH [^]]+\]' | \
    sed 's/\[GROWTH \/autonomous-/growth:/; s/\[EVO #[0-9]* /evo:/; s/\[AUTOSYNTH \/autonomous-/autosynth:/' | \
    sed 's/\].*//' | \
    sort | \
    uniq -c | \
    sort -rn | \
    head -n "$top_n" | \
    awk '{printf "%s\t%d\n", $2, $1}'