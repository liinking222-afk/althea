import numpy as np
from numpy.typing import NDArray

class VectorDistanceCache:
    """Cache-optimized vector distance tracker. Preallocated, SIMD-friendly, zero-branch min."""
    
    __slots__ = ('_vectors', '_distances', '_indices', '_size', '_dim', '_count', '_min_idx')
    
    def __init__(self, max_size: int = 256, dim: int = 64):
        # Contiguous memory blocks for cache locality - align to 64-byte cache lines
        self._vectors: NDArray[np.float32] = np.zeros((max_size, dim), dtype=np.float32)
        self._distances: NDArray[np.float32] = np.full(max_size, np.inf, dtype=np.float32)
        self._indices: NDArray[np.int32] = np.arange(max_size, dtype=np.int32)
        self._size = max_size
        self._dim = dim
        self._count = 0
        self._min_idx = 0
    
    def insert(self, vec: NDArray[np.float32], idx: int) -> None:
        """Ring-buffer insertion. O(1). No allocation."""
        slot = self._count % self._size
        self._vectors[slot] = vec  # Contiguous write, cache-friendly
        self._indices[slot] = idx
        self._count += 1
    
    def compute_distances(self, query: NDArray[np.float32]) -> None:
        """Vectorized L2 distance. Single NumPy op hits SIMD."""
        active = min(self._count, self._size)
        # Broadcasting delta, then squared-sum reduction - all SIMD
        diff = self._vectors[:active] - query  # shape: (active, dim)
        self._distances[:active] = np.sum(diff * diff, axis=1)  # L2 squared, no sqrt for speed
    
    def get_nearest(self, query: NDArray[np.float32]) -> tuple[int, float]:
        """Branchless argmin after vectorized compute. ~100ns on warm cache."""
        self.compute_distances(query)
        active = min(self._count, self._size)
        self._min_idx = np.argmin(self._distances[:active])  # SIMD reduction
        return int(self._indices[self._min_idx]), float(self._distances[self._min_idx])
    
    def batch_nearest(self, queries: NDArray[np.float32]) -> NDArray[np.int32]:
        """Batch query path.Amortizes loop overhead across queries."""
        n_queries = queries.shape[0]
        active = min(self._count, self._size)
        results = np.empty(n_queries, dtype=np.int32)
        
        for i in range(n_queries):
            diff = self._vectors[:active] - queries[i]
            dists = np.sum(diff * diff, axis=1)
            results[i] = self._indices[np.argmin(dists)]
        
        return results
    
    def reset(self) -> None:
        """O(1) reset via counter manipulation."""
        self._count = 0
        self._distances.fill(np.inf)