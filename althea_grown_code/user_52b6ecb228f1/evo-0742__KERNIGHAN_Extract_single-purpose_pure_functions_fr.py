#!/usr/bin/env python3
"""
kernighan_pure_utils.py - Single-purpose composable utilities
Each function does ONE thing. Names ARE the documentation.
"""

def read_csv_to_dict_list(filepath):
    """Read CSV file, return list of dictionaries."""
    import csv
    with open(filepath, 'r') as f:
        return list(csv.DictReader(f))

def compute_column_mean(dict_list, column_name):
    """Calculate mean of numeric column."""
    values = [float(row[column_name]) for row in dict_list if column_name in row]
    return sum(values) / len(values) if values else 0.0

def compute_column_median(dict_list, column_name):
    """Calculate median of numeric column."""
    values = sorted([float(row[column_name]) for row in dict_list if column_name in row])
    n = len(values)
    if n == 0: return 0.0
    return values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2

def filter_rows_by_key_value(dict_list, key, value):
    """Filter rows where key equals value."""
    return [row for row in dict_list if row.get(key) == value]

def extract_column(dict_list, column_name):
    """Extract single column as list."""
    return [row[column_name] for row in dict_list if column_name in row]

def group_by_key(dict_list, key):
    """Group rows by key value, return dictionary of lists."""
    groups = {}
    for row in dict_list:
        k = row.get(key)
        if k not in groups:
            groups[k] = []
        groups[k].append(row)
    return groups

def write_dict_list_to_csv(dict_list, filepath):
    """Write list of dictionaries to CSV file."""
    import csv
    if not dict_list: return
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=dict_list[0].keys())
        writer.writeheader()
        writer.writerows(dict_list)

def pipe(*functions):
    """Compose functions left-to-right (Unix pipe style)."""
    def composed(x):
        result = x
        for f in functions:
            result = f(result)
        return result
    return composed

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        data = [{'x': '1', 'y': 'a'}, {'x': '2', 'y': 'b'}, {'x': '3', 'y': 'a'}]
        print(compute_column_mean(data, 'x'))
        print(filter_rows_by_key_value(data, 'y', 'a'))
        print(extract_column(data, 'x'))