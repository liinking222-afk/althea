#!/bin/bash
# /autonomous-log-pattern-analyzer
# WOZ constraint: pure pipe operations, no intermediate files, minimal memory

analyze_usage_log() {
  awk '
    BEGIN {
      FS="|"
      print "# ALTHEA Usage Pattern Analysis"
      print "# Generated: " strftime("%Y-%m-%d %H:%M:%S")
      print ""
    }
    
    /^\[LOG\]/ {
      # Extract: timestamp, module, params
      gsub(/^\[LOG\] /, "")
      timestamp = $1
      module = $2
      
      # Count invocations
      count[module]++
      
      # Track first and last seen
      if (first[module] == "") first[module] = timestamp
      last[module] = timestamp
      
      # Extract hour for temporal pattern
      if (match(timestamp, /[0-9]{2}:[0-9]{2}/)) {
        hour = substr(timestamp, RSTART, 2)
        hourly[module, hour]++
      }
    }
    
    END {
      # Frequency ranking
      print "## FREQUENCY RANK"
      print "Count\tModule\tFirst\tLast"
      
      # Sort by count (descending)
      n = asorti(count, sorted_modules)
      for (i = n; i >= 1; i--) {
        mod = sorted_modules[i]
        # Bubble sort to get top by count
      }
      
      # Simple output - sorted later via pipe
      for (mod in count) {
        printf "%05d\t%s\t%s\t%s\n", count[mod], mod, first[mod], last[mod]
      }
      
      print ""
      print "## TEMPORAL HOTSPOTS"
      for (key in hourly) {
        split(key, parts, SUBSEP)
        printf "%s\t%02d:00\t%d\n", parts[1], parts[2], hourly[key]
      }
    }
  ' | sort -rn
}

# Read from stdin or file
if [ -t 0 ]; then
  echo "Usage: cat usage.log | $0" >&2
  exit 1
fi

analyze_usage_log