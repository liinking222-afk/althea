#!/usr/bin/env python3
import mmap
import struct
import hashlib
import os
from pathlib import Path

CACHE_PATH = Path("/tmp/althea_autosynth_sigs.mmap")
CACHE_SIZE = 1024 * 1024  # 1MB, 16384 slots of 64 bytes each
SLOT_SIZE = 64
MAGIC = 0x414C5448  # "ALTH"

def init_cache():
    if not CACHE_PATH.exists():
        with open(CACHE_PATH, "wb") as f:
            f.write(b'\x00' * CACHE_SIZE)
    fd = os.open(CACHE_PATH, os.O_RDWR)
    mm = mmap.mmap(fd, CACHE_SIZE, access=mmap.ACCESS_WRITE)
    if struct.unpack("I", mm[0:4])[0] != MAGIC:
        mm[0:4] = struct.pack("I", MAGIC)
        mm[4:8] = struct.pack("I", 0)  # generation counter
    return mm, fd

def sig_hash(module_type: str, intent: str) -> bytes:
    key = f"{module_type}:{intent}".encode()
    return hashlib.blake2b(key, digest_size=32).digest()

def slot_index(sig: bytes) -> int:
    return struct.unpack("I", sig[:4])[0] % ((CACHE_SIZE - 8) // SLOT_SIZE)

def check_or_insert(mm, sig: bytes) -> bool:
    """Returns True if already exists (dedupe), False if newly inserted."""
    idx = slot_index(sig)
    offset = 8 + idx * SLOT_SIZE
    
    stored_sig = mm[offset:offset + 32]
    if stored_sig == sig:
        # Hit: increment counter
        count = struct.unpack("I", mm[offset + 32:offset + 36])[0]
        mm[offset + 32:offset + 36] = struct.pack("I", count + 1)
        return True
    elif stored_sig == b'\x00' * 32:
        # Empty slot: insert
        mm[offset:offset + 32] = sig
        mm[offset + 32:offset + 36] = struct.pack("I", 1)
        mm[offset + 36:offset + 44] = struct.pack("Q", int(os.times().elapsed * 1000))
        gen = struct.unpack("I", mm[4:8])[0]
        mm[4:8] = struct.pack("I", gen + 1)
        return False
    else:
        # Collision: allow (hash table degrades gracefully)
        return False

def should_spawn(module_type: str, intent: str) -> bool:
    mm, fd = init_cache()
    sig = sig_hash(module_type, intent)
    exists = check_or_insert(mm, sig)
    mm.close()
    os.close(fd)
    return not exists

if __name__ == "__main__":
    print(should_spawn("orbital-propagation", "Propagate satellite orbits from TLE"))
    print(should_spawn("orbital-propagation", "Propagate satellite orbits from TLE"))
    print(should_spawn("resonance-basin", "Different intent"))