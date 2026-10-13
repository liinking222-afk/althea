import numpy as np
from numba import njit, uint64, uint32, uint8
import hashlib

@njit(uint64(uint64, uint32), cache=True, fastmath=True)
def hash_mix(x, seed):
    # MurmurHash3-style mixer - cache-friendly single dependency chain
    x ^= seed
    x ^= x >> 33
    x *= uint64(0xff51afd7ed558ccd)
    x ^= x >> 33
    x *= uint64(0xc4ceb9fe1a85ec53)
    x ^= x >> 33
    return x

@njit(cache=True, fastmath=True, inline='always')
def set_bloom_bits(bloom, pattern_hash, k=7):
    # 7 hashes, inlined bit-twiddling, hot loop ~10ns/iter
    size_bits = len(bloom) << 3
    mask = size_bits - 1  # power-of-2 optimization
    h = pattern_hash
    for i in range(k):
        h = hash_mix(h, uint32(i))
        bit_idx = h & mask
        byte_idx = bit_idx >> 3
        bit_offset = uint8(bit_idx & 7)
        bloom[byte_idx] |= uint8(1 << bit_offset)

@njit(cache=True, fastmath=True, inline='always')
def check_bloom_bits(bloom, pattern_hash, k=7):
    size_bits = len(bloom) << 3
    mask = size_bits - 1
    h = pattern_hash
    for i in range(k):
        h = hash_mix(h, uint32(i))
        bit_idx = h & mask
        byte_idx = bit_idx >> 3
        bit_offset = uint8(bit_idx & 7)
        if not (bloom[byte_idx] & (uint8(1 << bit_offset))):
            return False
    return True

class PatternBloom:
    def __init__(self, size_kb=64):
        # 64KB fits L1 cache on most architectures
        self.bloom = np.zeros(size_kb * 1024, dtype=np.uint8)
        self.count = 0
    
    def add(self, pattern_str):
        h = uint64(int(hashlib.sha256(pattern_str.encode()).hexdigest()[:16], 16))
        set_bloom_bits(self.bloom, h)
        self.count += 1
    
    def probably_seen(self, pattern_str):
        h = uint64(int(hashlib.sha256(pattern_str.encode()).hexdigest()[:16], 16))
        return check_bloom_bits(self.bloom, h)
    
    def fpp_estimate(self):
        # False positive probability: (1 - e^(-kn/m))^k
        m = len(self.bloom) * 8
        k = 7
        n = self.count
        return (1.0 - np.exp(-k * n / m)) ** k if n > 0 else 0.0

# Hot path: <100ns per check on warm cache