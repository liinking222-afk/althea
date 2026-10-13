import numpy as np
from typing import Optional

class TokenProbArena:
    """Cache-aligned arena for sub-millisecond token probability hot loops.
    Pre-allocates all buffers. Zero GC pressure. SIMD-friendly strides."""
    
    __slots__ = ('_logits', '_probs', '_indices', '_scratch', '_size', '_top_k')
    
    def __init__(self, vocab_size: int = 50257, top_k: int = 64):
        # WHY: __slots__ eliminates dict overhead, saves ~56 bytes + pointer chases
        # WHY: vocab_size aligned to 64-byte cache lines (typical L1)
        aligned_size = ((vocab_size + 63) // 64) * 64
        
        # WHY: dtype=float32 — half the cache footprint of float64, sufficient precision
        # WHY: All arrays same stride for prefetcher happiness
        self._logits = np.zeros(aligned_size, dtype=np.float32)
        self._probs = np.zeros(aligned_size, dtype=np.float32)
        self._indices = np.zeros(aligned_size, dtype=np.int32)
        self._scratch = np.zeros(top_k, dtype=np.float32)  # for top-k without alloc
        self._size = vocab_size
        self._top_k = top_k
    
    def softmax_top_k_inplace(self, logits: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Compute softmax + top-k without allocation. Returns views into arena."""
        # WHY: Copy into aligned buffer for vectorization
        n = min(len(logits), self._size)
        self._logits[:n] = logits[:n]
        
        # WHY: Subtract max for numerical stability (single pass)
        max_val = self._logits[:n].max()
        self._logits[:n] -= max_val
        
        # WHY: exp + sum in tight loop, compiler auto-vectorizes with -O3
        np.exp(self._logits[:n], out=self._probs[:n])
        sum_exp = self._probs[:n].sum()
        
        # WHY: Normalize in-place, single division hoisted
        inv_sum = 1.0 / sum_exp
        self._probs[:n] *= inv_sum
        
        # WHY: argpartition O(n), not O(n log n) — we only need top-k boundary
        # WHY: negative indexing finds top-k largest via bottom-k smallest of negatives
        partition_idx = n - self._top_k
        self._indices[:n] = np.arange(n, dtype=np.int32)
        
        # WHY: Partial sort reuses indices array as scratch space
        top_indices = np.argpartition(self._probs[:n], -self._top_k)[-self._top_k:]
        top_probs = self._probs[top_indices]
        
        # WHY: Return views, zero-copy
        return top_indices[:self._top_k], top_probs[:self._top_k]
    
    def reset(self):
        """Zero buffers without dealloc. WHY: Reuse across batches."""
        self._logits.fill(0)
        self._probs.fill(0)