#!/bin/bash
# event_dedupe_stream - UNIX-style memory event deduplicator
# Reads events from stdin, outputs unique canonical forms to stdout

declare -A seen_hashes

hash_event() {
    # Extract semantic core: strip timestamps, IDs, version numbers
    echo "$1" | sed -E 's/[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]+Z//g; s/\#[0-9]+//g; s/v[0-9]+\.[0-9]+\.[0-9]+//g; s/\s+/ /g' | tr -d ' ' | md5sum | cut -d' ' -f1
}

canonicalize() {
    # Emit canonical form: sorted fields, normalized spacing
    echo "$1" | sed -E 's/^\[//; s/\]$//' | tr -s ' ' | sort -t' ' -k1
}

while IFS= read -r line; do
    if [[ -z "$line" || "$line" =~ ^# ]]; then
        continue
    fi
    
    hash=$(hash_event "$line")
    
    if [[ -z "${seen_hashes[$hash]}" ]]; then
        seen_hashes[$hash]=1
        canonicalize "$line"
    fi
done

# Usage: tail -f memory.log | ./event_dedupe_stream | tee -a canonical_memory.log