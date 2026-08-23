# /core/memory/batch_fnv1a_hash.py
# Carmack principle: batch the hottest loop, eliminate abstraction tax
# FNV-1a constants for 64-bit - precomputed, inlined everywhere
FNV_OFFSET_BASIS = 0xcbf29ce484222325
FNV_PRIME = 0x100000001b3

def batch_hash_entries(entries: list[str]) -> list[int]:
    """Compute FNV-1a hashes for multiple entries in single tight loop.
    
    WHY: Memory dedup hits this thousands of times per context. Traditional
    per-string hashing creates N function calls + N loop setups. We fuse
    into one hot loop with manual unrolling hints via stride patterns.
    
    Cache locality: process 4 strings before moving to next batch segment.
    Math density: bitwise ops only, no branches in inner kernel.
    """
    hashes = [FNV_OFFSET_BASIS] * len(entries)
    
    # Stride-4 unrolling for CPU pipeline parallelism
    i = 0
    limit = len(entries) & ~3  # Round down to multiple of 4
    
    while i < limit:
        # Process 4 hashes simultaneously - exploits ILP
        h0, h1, h2, h3 = hashes[i], hashes[i+1], hashes[i+2], hashes[i+3]
        s0, s1, s2, s3 = entries[i], entries[i+1], entries[i+2], entries[i+3]
        
        # Encode strings to bytes once per batch
        b0, b1, b2, b3 = s0.encode(), s1.encode(), s2.encode(), s3.encode()
        
        # Find max length for this batch to vectorize
        max_len = max(len(b0), len(b1), len(b2), len(b3))
        
        for j in range(max_len):
            # Branchless byte extraction (0 if index OOB)
            byte0 = b0[j] if j < len(b0) else 0
            byte1 = b1[j] if j < len(b1) else 0
            byte2 = b2[j] if j < len(b2) else 0
            byte3 = b3[j] if j < len(b3) else 0
            
            # FNV-1a kernel: xor then multiply (no branches)
            h0 = ((h0 ^ byte0) * FNV_PRIME) & 0xffffffffffffffff
            h1 = ((h1 ^ byte1) * FNV_PRIME) & 0xffffffffffffffff
            h2 = ((h2 ^ byte2) * FNV_PRIME) & 0xffffffffffffffff
            h3 = ((h3 ^ byte3) * FNV_PRIME) & 0xffffffffffffffff
        
        hashes[i:i+4] = [h0, h1, h2, h3]
        i += 4
    
    # Tail cleanup for remaining entries
    while i < len(entries):
        h = hashes[i]
        for byte in entries[i].encode():
            h = ((h ^ byte) * FNV_PRIME) & 0xffffffffffffffff
        hashes[i] = h
        i += 1
    
    return hashes