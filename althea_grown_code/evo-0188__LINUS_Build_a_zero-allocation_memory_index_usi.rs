use std::collections::HashMap;
use std::fs;
use std::path::Path;

const MAX_MODULES: usize = 512;
const MAX_TOKENS: usize = 8192;

#[repr(packed)]
struct ModuleRef {
    offset: u32,
    length: u16,
    hash: u16,
}

struct CompactIndex {
    refs: [ModuleRef; MAX_MODULES],
    tokens: [u64; MAX_TOKENS],
    ref_count: u16,
    token_count: u16,
}

impl CompactIndex {
    fn new() -> Self {
        CompactIndex {
            refs: [ModuleRef { offset: 0, length: 0, hash: 0 }; MAX_MODULES],
            tokens: [0u64; MAX_TOKENS],
            ref_count: 0,
            token_count: 0,
        }
    }

    fn hash_token(s: &str) -> u64 {
        let mut h = 0xcbf29ce484222325u64;
        for b in s.bytes() {
            h ^= b as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
        h
    }

    fn add_module(&mut self, path: &str, content: &str) -> bool {
        if self.ref_count >= MAX_MODULES as u16 {
            return false;
        }
        let offset = self.ref_count as u32 * 4096;
        let hash = (Self::hash_token(path) & 0xFFFF) as u16;
        self.refs[self.ref_count as usize] = ModuleRef {
            offset,
            length: content.len().min(65535) as u16,
            hash,
        };
        for word in content.split_whitespace().take(32) {
            if self.token_count < MAX_TOKENS as u16 {
                self.tokens[self.token_count as usize] = Self::hash_token(word);
                self.token_count += 1;
            }
        }
        self.ref_count += 1;
        true
    }

    fn find(&self, query: &str) -> Vec<usize> {
        let qhash = Self::hash_token(query);
        let mut results = Vec::new();
        for i in 0..self.token_count as usize {
            if self.tokens[i] == qhash {
                results.push(i / 32);
            }
        }
        results
    }

    fn memory_bytes(&self) -> usize {
        std::mem::size_of::<Self>()
    }
}

fn main() {
    let mut index = CompactIndex::new();
    println!("Index size: {} bytes", index.memory_bytes());
}