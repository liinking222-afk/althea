use std::mem::MaybeUninit;

const ARENA_SIZE: usize = 4096;
const MAX_RESIDUES: usize = 256;

#[repr(C)]
struct ResidueArena {
    tokens: [u64; MAX_RESIDUES],
    weights: [f32; MAX_RESIDUES],
    contexts: [u32; MAX_RESIDUES],
    timestamps: [u64; MAX_RESIDUES],
    head: usize,
    count: usize,
}

impl ResidueArena {
    fn new() -> Self {
        unsafe {
            ResidueArena {
                tokens: MaybeUninit::zeroed().assume_init(),
                weights: MaybeUninit::zeroed().assume_init(),
                contexts: MaybeUninit::zeroed().assume_init(),
                timestamps: MaybeUninit::zeroed().assume_init(),
                head: 0,
                count: 0,
            }
        }
    }

    #[inline]
    fn push(&mut self, token: u64, weight: f32, context: u32, timestamp: u64) {
        let idx = self.head;
        self.tokens[idx] = token;
        self.weights[idx] = weight;
        self.contexts[idx] = context;
        self.timestamps[idx] = timestamp;
        self.head = (self.head + 1) & (MAX_RESIDUES - 1);
        if self.count < MAX_RESIDUES {
            self.count += 1;
        }
    }

    #[inline]
    fn query_by_weight_threshold(&self, threshold: f32) -> impl Iterator<Item = usize> + '_ {
        (0..self.count).filter(move |&i| self.weights[i] >= threshold)
    }

    #[inline]
    fn compress_dead(&mut self, age_threshold: u64, current_time: u64) {
        let mut write_idx = 0;
        for read_idx in 0..self.count {
            if current_time - self.timestamps[read_idx] <= age_threshold {
                if write_idx != read_idx {
                    self.tokens[write_idx] = self.tokens[read_idx];
                    self.weights[write_idx] = self.weights[read_idx];
                    self.contexts[write_idx] = self.contexts[read_idx];
                    self.timestamps[write_idx] = self.timestamps[read_idx];
                }
                write_idx += 1;
            }
        }
        self.count = write_idx;
        self.head = write_idx & (MAX_RESIDUES - 1);
    }

    #[inline]
    fn weight_sum_simd(&self) -> f32 {
        self.weights[0..self.count].iter().sum()
    }
}

fn main() {
    let mut arena = ResidueArena::new();
    arena.push(0xdeadbeef, 0.95, 42, 1000);
    arena.push(0xcafebabe, 0.23, 17, 1050);
    arena.compress_dead(100, 1200);
}