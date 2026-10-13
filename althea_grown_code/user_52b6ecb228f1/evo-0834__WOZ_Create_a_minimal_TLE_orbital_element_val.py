#!/usr/bin/env python3
"""TLE validator - hardware-level gate before expensive SGP4 computation"""

import sys
import re
from typing import Optional, Tuple

def checksum_tle_line(line: str) -> int:
    """Compute TLE checksum: sum all digits, treat '-' as 1, mod 10"""
    total = sum(int(c) if c.isdigit() else 1 if c == '-' else 0 for c in line[:68])
    return total % 10

def validate_tle(line1: str, line2: str, name: Optional[str] = None) -> Tuple[bool, str]:
    """Validate TLE format and checksums before expensive propagation"""
    
    # Length check (hard gate)
    if len(line1) != 69 or len(line2) != 69:
        return False, f"Invalid length: L1={len(line1)} L2={len(line2)} (need 69)"
    
    # Line number check
    if line1[0] != '1' or line2[0] != '2':
        return False, f"Line markers wrong: '{line1[0]}' '{line2[0]}'"
    
    # Checksum validation (catch corruption early)
    ck1_expected = int(line1[68])
    ck1_computed = checksum_tle_line(line1)
    if ck1_computed != ck1_expected:
        return False, f"L1 checksum fail: got {ck1_computed}, expected {ck1_expected}"
    
    ck2_expected = int(line2[68])
    ck2_computed = checksum_tle_line(line2)
    if ck2_computed != ck2_expected:
        return False, f"L2 checksum fail: got {ck2_computed}, expected {ck2_expected}"
    
    # Satellite number match
    satnum1 = line1[2:7].strip()
    satnum2 = line2[2:7].strip()
    if satnum1 != satnum2:
        return False, f"Sat number mismatch: L1={satnum1} L2={satnum2}"
    
    # Basic field format checks (critical fields only)
    try:
        epoch = float(line1[18:32])
        if not (0 <= epoch <= 99999.99999999):
            return False, f"Epoch out of range: {epoch}"
        
        inclination = float(line2[8:16])
        if not (0 <= inclination <= 180):
            return False, f"Inclination invalid: {inclination}"
            
        mean_motion = float(line2[52:63])
        if mean_motion <= 0:
            return False, f"Mean motion non-positive: {mean_motion}"
    except ValueError as e:
        return False, f"Field parse error: {e}"
    
    return True, "VALID"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: tle-validate.py <line1> <line2> [name]", file=sys.stderr)
        sys.exit(1)
    
    valid, msg = validate_tle(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    print(msg)
    sys.exit(0 if valid else 1)