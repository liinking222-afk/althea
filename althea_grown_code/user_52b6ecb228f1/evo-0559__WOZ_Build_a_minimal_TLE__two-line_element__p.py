def parse_tle(line1, line2):
    """Parse TLE with bit-level precision. Every byte counts."""
    def extract(s, start, end): return s[start:end].strip()
    def float_field(s, start, end):
        val = extract(s, start, end)
        if not val or val == '.': return 0.0
        if val[0] in '+-' and '.' not in val[1:]:
            # Assumed decimal point format: "-12345-6" means -0.12345e-6
            base, exp = val[:-2], val[-2:]
            return float(base[0] + '0.' + base[1:]) * (10 ** int(exp))
        return float(val)
    
    # Line 1: catalog#, epoch, ndot/2, nddot/6, bstar, ephemeris, element#
    catalog_num = int(extract(line1, 2, 7))
    classification = line1[7]
    epoch_year = int(extract(line1, 18, 20))
    epoch_day = float_field(line1, 20, 32)
    mean_motion_dot = float_field(line1, 33, 43)
    mean_motion_ddot = float_field(line1, 44, 52)
    bstar = float_field(line1, 53, 61)
    ephemeris_type = int(extract(line1, 62, 63) or '0')
    element_num = int(extract(line1, 64, 68))
    
    # Line 2: inclination, raan, eccentricity, arg_perigee, mean_anomaly, mean_motion, rev#
    inclination = float_field(line2, 8, 16)
    raan = float_field(line2, 17, 25)
    eccentricity = float('0.' + extract(line2, 26, 33))
    arg_perigee = float_field(line2, 34, 42)
    mean_anomaly = float_field(line2, 43, 51)
    mean_motion = float_field(line2, 52, 63)
    revolution_num = int(extract(line2, 63, 68))
    
    return {
        'catalog': catalog_num, 'class': classification,
        'epoch_yr': epoch_year + (1900 if epoch_year > 57 else 2000),
        'epoch_day': epoch_day, 'ndot': mean_motion_dot * 2,
        'nddot': mean_motion_ddot * 6, 'bstar': bstar,
        'inc': inclination, 'raan': raan, 'ecc': eccentricity,
        'argp': arg_perigee, 'anom': mean_anomaly, 'motion': mean_motion,
        'rev': revolution_num
    }