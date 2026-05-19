#!/bin/bash
# stream_modules.sh - UNIX-style module metadata processor
# Usage: ./stream_modules.sh [filter] [transform]

MODULE_DIR="${ALTHEA_MODULE_DIR:-./.althea/modules}"
CACHE_FILE="/tmp/althea_module_stream.cache"

# Extract module metadata as line-delimited records
list_modules() {
    find "$MODULE_DIR" -name "*.js" -o -name "*.py" -o -name "*.ts" | while read -r file; do
        name=$(basename "$file" | cut -d. -f1)
        version=$(grep -oP "version['\"]?\s*[:=]\s*['\"]?\K[0-9.]+" "$file" | head -1)
        exports=$(grep -oP "export (function|const|class) \K\w+" "$file" | tr '\n' ',' | sed 's/,$//')
        size=$(wc -l < "$file")
        echo "$name|${version:-0.0.0}|$exports|$size|$file"
    done
}

# Filter by pattern
filter_stream() {
    if [ -n "$1" ]; then
        grep -i "$1"
    else
        cat
    fi
}

# Transform operations
transform_stream() {
    case "$1" in
        count) wc -l ;;
        exports) cut -d'|' -f3 | tr ',' '\n' | sort -u ;;
        heavy) awk -F'|' '$4 > 50 {print $1 " (" $4 " lines)"}' ;;
        versions) cut -d'|' -f1,2 | column -t -s'|' ;;
        paths) cut -d'|' -f5 ;;
        *) cat ;;
    esac
}

# Main pipeline
list_modules | tee "$CACHE_FILE" | filter_stream "$1" | transform_stream "$2"