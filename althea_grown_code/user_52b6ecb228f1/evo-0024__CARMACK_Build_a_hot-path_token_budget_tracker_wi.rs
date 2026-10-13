use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};

#[repr(align(64))] // Cache line alignment - prevent false sharing
pub struct TokenBudgetTracker {
    total_budget: AtomicU64,
    consumed: AtomicU64,
    checkpoint_ring: [AtomicU64; 8], // Power-of-2 for fast modulo via bitmasking
    ring_idx: AtomicUsize,
}

impl TokenBudgetTracker {
    #[inline(always)]
    pub const fn new(budget: u64) -> Self {
        const ZERO: AtomicU64 = AtomicU64::new(0);
        Self {
            total_budget: AtomicU64::new(budget),
            consumed: AtomicU64::new(0),
            checkpoint_ring: [ZERO; 8],
            ring_idx: AtomicUsize::new(0),
        }
    }

    // Hot path: relaxed ordering, no branching except return
    #[inline(always)]
    pub fn try_consume(&self, tokens: u64) -> bool {
        let current = self.consumed.fetch_add(tokens, Ordering::Relaxed);
        let budget = self.total_budget.load(Ordering::Relaxed);
        current + tokens <= budget // Single branch prediction friendly check
    }

    // Fast remaining check without division
    #[inline(always)]
    pub fn remaining(&self) -> u64 {
        let budget = self.total_budget.load(Ordering::Relaxed);
        let consumed = self.consumed.load(Ordering::Relaxed);
        budget.saturating_sub(consumed) // No branch, saturates to 0
    }

    // Checkpoint with ring buffer - no allocation, no locks
    #[inline]
    pub fn checkpoint(&self) -> u64 {
        let consumed = self.consumed.load(Ordering::Acquire);
        let idx = self.ring_idx.fetch_add(1, Ordering::Relaxed) & 0x7; // Fast mod 8
        self.checkpoint_ring[idx].store(consumed, Ordering::Release);
        consumed
    }

    // Fast delta since last checkpoint - O(1) ring scan
    #[inline]
    pub fn delta_since_checkpoint(&self, checkpoint: u64) -> u64 {
        self.consumed.load(Ordering::Relaxed).saturating_sub(checkpoint)
    }

    // Fast utilization as fixed-point ratio (avoid float ops)
    // Returns basis points: 10000 = 100%, 5000 = 50%
    #[inline]
    pub fn utilization_bp(&self) -> u64 {
        let consumed = self.consumed.load(Ordering::Relaxed);
        let budget = self.total_budget.load(Ordering::Relaxed);
        if budget == 0 { return 10000; }
        (consumed * 10000) / budget // Integer math, predictable latency
    }

    // Reset for new evolution cycle - rare, can be slower
    pub fn reset(&self, new_budget: u64) {
        self.total_budget.store(new_budget, Ordering::Release);
        self.consumed.store(0, Ordering::Release);
        self.ring_idx.store(0, Ordering::Release);
    }
}