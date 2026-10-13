#!/usr/bin/env python3
"""tle_filter.py - Transform TLE data into pipe-friendly plain text streams"""
import sys
import re
from datetime import datetime

def parse_tle_line0(line):
    """Extract satellite name from line 0"""
    return line.strip()

def parse_tle_line1(line):
    """Extract key orbital elements from TLE line 1"""
    catalog = line[2:7].strip()
    epoch_year = int(line[18:20])
    epoch_day = float(line[20:32])
    year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year
    return catalog, year, epoch_day

def parse_tle_line2(line):
    """Extract inclination, RAAN, eccentricity, arg_perigee, mean_anomaly, mean_motion"""
    incl = float(line[8:16])
    raan = float(line[17:25])
    ecc = float("0." + line[26:33])
    arg_perigee = float(line[34:42])
    mean_anom = float(line[43:51])
    mean_motion = float(line[52:63])
    return incl, raan, ecc, arg_perigee, mean_anom, mean_motion

def tle_to_tsv(input_stream, output_stream, format_type="tsv"):
    """Convert TLE format to TSV stream"""
    lines = []
    
    if format_type == "tsv":
        output_stream.write("NAME\tCATALOG\tEPOCH_YEAR\tEPOCH_DAY\tINCL\tRAAN\tECC\tARG_PER\tMEAN_ANOM\tMEAN_MOTION\n")
    
    for line in input_stream:
        line = line.rstrip('\n')
        if not line:
            continue
        lines.append(line)
        
        if len(lines) == 3:
            name = parse_tle_line0(lines[0])
            catalog, year, epoch_day = parse_tle_line1(lines[1])
            incl, raan, ecc, arg_per, mean_anom, mean_motion = parse_tle_line2(lines[2])
            
            if format_type == "tsv":
                output_stream.write(f"{name}\t{catalog}\t{year}\t{epoch_day:.8f}\t{incl:.4f}\t{raan:.4f}\t{ecc:.7f}\t{arg_per:.4f}\t{mean_anom:.4f}\t{mean_motion:.8f}\n")
            
            lines = []

if __name__ == "__main__":
    fmt = sys.argv[1] if len(sys.argv) > 1 else "tsv"
    tle_to_tsv(sys.stdin, sys.stdout, fmt)