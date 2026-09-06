use std::collections::HashSet;
use std::sync::RwLock;

const PRIME: u64 = 0x517cc1b727220a95;
const BATCH_SIZE: usize = 16;

static SIGNATURE_CACHE: RwLock<HashSet<u64>> = RwLock::new(HashSet::new());

#[inline(always)]
fn hash_signature(module: &str, context: &str) -> u64 {
    let mut h = PRIME;
    let bytes = module.as_bytes();
    let ctx_bytes = context.as_bytes();
    
    // Unrolled hot loop - process 8 bytes at a time
    let len = bytes.len();
    let mut i = 0;
    while i + 8 <= len {
        h ^= u64::from_le_bytes(bytes[i..i+8].try_into().unwrap());
        h = h.wrapping_mul(PRIME);
        i += 8;
    }
    while i < len {
        h ^= bytes[i] as u64;
        h = h.wrapping_mul(PRIME);
        i += 1;
    }
    
    // Mix context with single pass
    for &b in ctx_bytes {
        h ^= b as u64;
        h = h.rotate_left(5);
    }
    
    h
}

#[inline(always)]
pub fn batch_check_unique(signatures: &[(String, String)]) -> Vec<bool> {
    let mut results = Vec::with_capacity(signatures.len());
    let mut hashes = Vec::with_capacity(BATCH_SIZE);
    
    for (module, context) in signatures {
        hashes.push(hash_signature(module, context));
        
        if hashes.len() == BATCH_SIZE {
            // Process batch with single lock acquire
            let cache = SIGNATURE_CACHE.read().unwrap();
            for &h in &hashes {
                results.push(!cache.contains(&h));
            }
            drop(cache);
            hashes.clear();
        }
    }
    
    // Process remainder
    if !hashes.is_empty() {
        let cache = SIGNATURE_CACHE.read().unwrap();
        for &h in &hashes {
            results.push(!cache.contains(&h));
        }
    }
    
    results
}

#[inline(always)]
pub fn register_spawned(module: &str, context: &str) {
    let h = hash_signature(module, context);
    SIGNATURE_CACHE.write().unwrap().insert(h);
}