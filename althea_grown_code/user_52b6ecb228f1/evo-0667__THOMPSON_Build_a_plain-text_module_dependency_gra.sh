#!/usr/bin/env bash
# /autonomous-module-graph
# Reads Althea module files, extracts dependencies, outputs graphviz dot format
# Usage: ./autonomous-module-graph [module_dir] | dot -Tpng > graph.png

MODULE_DIR="${1:-.}"

echo "digraph modules {"
echo "  rankdir=LR;"
echo "  node [shape=box, style=rounded];"

find "$MODULE_DIR" -type f \( -name "*.py" -o -name "*.js" -o -name "*.sh" -o -name "*.ts" -o -name "*.go" -o -name "*.rs" \) | while read -r file; do
  module_name=$(basename "$file" | sed 's/\.[^.]*$//')
  
  # Extract import/require/use statements
  grep -E "^(import|from|require\(|use |mod )" "$file" 2>/dev/null | \
    sed -E 's/.*["\x27]([^"\x27/]+)["\x27].*/\1/' | \
    grep -v "^$" | \
    sort -u | \
    while read -r dep; do
      # Skip standard library references
      if ! echo "$dep" | grep -qE "^(os|sys|re|json|time|fs|path|std|core)$"; then
        echo "  \"$module_name\" -> \"$dep\";"
      fi
    done
  
  # Check for function calls to other modules
  grep -oE "(/[a-z-]+)" "$file" 2>/dev/null | \
    sed 's|^/||' | \
    sort -u | \
    while read -r call; do
      if [ "$call" != "$module_name" ] && [ -n "$call" ]; then
        echo "  \"$module_name\" -> \"$call\" [style=dashed];"
      fi
    done
done | sort -u

echo "}"