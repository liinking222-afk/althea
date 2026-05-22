#!/bin/bash
# semantic_pipe - UNIX-style semantic stream processor
# Reads concept clusters from stdin, outputs centroid coordinates to stdout

set -euo pipefail

cluster_extract() {
  awk '{for(i=1;i<=NF;i++) print $i}' | sort | uniq -c | sort -rn
}

centroid_compute() {
  awk '{sum+=$1; count++; terms=terms $2 ","} END {
    print "weight:" sum/count
    print "terms:" substr(terms, 1, length(terms)-1)
  }'
}

shift_vector() {
  local direction="${1:-north}"
  awk -v dir="$direction" 'BEGIN {
    split("north:0,1 south:0,-1 east:1,0 west:-1,0", dirs, " ")
    for(i in dirs) {split(dirs[i], d, ":"); split(d[2], v, ","); vec[d[1]"_x"]=v[1]; vec[d[1]"_y"]=v[2]}
  }
  /^weight:/ {w=$2}
  /^terms:/ {t=$2; print "shifted_weight:" w+vec[dir"_x"]*0.1; print "shifted_terms:" t; print "vector:" dir}'
}

migration_apply() {
  awk -F: '{
    if($1=="shifted_terms") {
      split($2, terms, ",")
      for(i in terms) if(length(terms[i])>0) print terms[i]
    }
  }'
}

case "${1:-detect}" in
  detect)
    cluster_extract | centroid_compute
    ;;
  migrate)
    cluster_extract | centroid_compute | shift_vector "${2:-north}" | migration_apply
    ;;
  *)
    echo "Usage: semantic_pipe {detect|migrate [direction]}" >&2
    exit 1
    ;;
esac