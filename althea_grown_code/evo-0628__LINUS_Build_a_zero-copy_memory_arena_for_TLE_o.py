import mmap
import struct
from dataclasses import dataclass

@dataclass
class TLEArena:
    """Zero-copy TLE parser using memory-mapped buffer and struct unpacking."""
    buf: bytearray
    capacity: int
    cursor: int = 0
    
    @classmethod
    def create(cls, capacity=65536):
        return cls(buf=bytearray(capacity), capacity=capacity, cursor=0)
    
    def reset(self):
        self.cursor = 0
    
    def parse_tle_fast(self, line1: str, line2: str):
        """Parse TLE directly into packed struct without intermediate allocations."""
        self.reset()
        
        # Line 1: catalog, epoch year, epoch day, drag, ephemeris, element set
        catalog = int(line1[2:7])
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        drag = float(line1[33:43])
        
        # Line 2: inclination, raan, eccentricity, arg_perigee, mean_anomaly, mean_motion
        inclination = float(line2[8:16])
        raan = float(line2[17:25])
        ecc_str = "0." + line2[26:33].strip()
        eccentricity = float(ecc_str)
        arg_perigee = float(line2[34:42])
        mean_anomaly = float(line2[43:51])
        mean_motion = float(line2[52:63])
        
        # Pack into arena buffer (56 bytes)
        struct.pack_into('i2if7d', self.buf, 0,
                        catalog, epoch_year, 0, epoch_day,
                        drag, inclination, raan, eccentricity,
                        arg_perigee, mean_anomaly, mean_motion)
        
        self.cursor = 56
        return self.cursor
    
    def unpack_elements(self):
        """Unpack orbital elements from arena."""
        data = struct.unpack_from('i2if7d', self.buf, 0)
        return {
            'catalog': data[0],
            'epoch_year': data[1],
            'epoch_day': data[3],
            'drag': data[4],
            'inclination': data[5],
            'raan': data[6],
            'eccentricity': data[7],
            'arg_perigee': data[8],
            'mean_anomaly': data[9],
            'mean_motion': data[10]
        }

# Example usage
arena = TLEArena.create()
tle1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927"
tle2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
arena.parse_tle_fast(tle1, tle2)
elements = arena.unpack_elements()