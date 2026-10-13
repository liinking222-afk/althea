use std::collections::HashMap;

const MAX_MODULES: usize = 256;

#[repr(C)]
struct ModuleGraph {
    adjacency: [u64; MAX_MODULES * 4],
    module_ids: [u32; MAX_MODULES],
    count: usize,
}

impl ModuleGraph {
    fn new() -> Self {
        Self {
            adjacency: [0u64; MAX_MODULES * 4],
            module_ids: [0u32; MAX_MODULES],
            count: 0,
        }
    }

    fn add_edge(&mut self, from: usize, to: usize) {
        let word_idx = (from * 4) + (to / 64);
        let bit_idx = to % 64;
        self.adjacency[word_idx] |= 1u64 << bit_idx;
    }

    fn has_edge(&self, from: usize, to: usize) -> bool {
        let word_idx = (from * 4) + (to / 64);
        let bit_idx = to % 64;
        (self.adjacency[word_idx] & (1u64 << bit_idx)) != 0
    }

    fn out_degree(&self, node: usize) -> u32 {
        let base = node * 4;
        (0..4).map(|i| self.adjacency[base + i].count_ones()).sum()
    }

    fn detect_bloat(&self, threshold: u32) -> Vec<usize> {
        (0..self.count)
            .filter(|&i| self.out_degree(i) > threshold)
            .collect()
    }

    fn find_cycles_dfs(&self, start: usize, visited: &mut [u8; MAX_MODULES], 
                       stack: &mut [u8; MAX_MODULES]) -> bool {
        visited[start] = 1;
        stack[start] = 1;

        for to in 0..self.count {
            if self.has_edge(start, to) {
                if visited[to] == 0 {
                    if self.find_cycles_dfs(to, visited, stack) {
                        return true;
                    }
                } else if stack[to] == 1 {
                    return true;
                }
            }
        }
        stack[start] = 0;
        false
    }

    fn has_cycles(&self) -> bool {
        let mut visited = [0u8; MAX_MODULES];
        let mut stack = [0u8; MAX_MODULES];
        
        for i in 0..self.count {
            if visited[i] == 0 && self.find_cycles_dfs(i, &mut visited, &mut stack) {
                return true;
            }
        }
        false
    }
}