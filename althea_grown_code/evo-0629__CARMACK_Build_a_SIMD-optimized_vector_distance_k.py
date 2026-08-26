import numpy as np
from numpy.typing import NDArray

# CARMACK: Cache-coherent vector ops. Minimize indirection. FP precision matters.
# Hot path for cosine/euclidean distance in embedding space — core TL bottleneck.

def distance_batch_optimized(
    queries: NDArray[np.float32],  # (n_queries, dim)
    database: NDArray[np.float32],  # (n_db, dim)
    metric: str = "cosine"
) -> NDArray[np.float32]:  # (n_queries, n_db)
    """
    Vectorized distance kernel. Aggressively inlined ops for CPU cache hits.
    Assumes C-contiguous float32. Non-negotiable for L1 locality.
    """
    assert queries.flags['C_CONTIGUOUS'] and database.flags['C_CONTIGUOUS']
    assert queries.dtype == database.dtype == np.float32
    
    n_q, dim = queries.shape
    n_db = database.shape[0]
    
    if metric == "cosine":
        # Normalize once, reuse — sqrt is expensive, amortize it
        q_norms = np.sqrt(np.sum(queries * queries, axis=1, keepdims=True))  # (n_q, 1)
        db_norms = np.sqrt(np.sum(database * database, axis=1))  # (n_db,)
        
        # Fused multiply-accumulate via matmul — let BLAS handle SIMD
        dots = np.matmul(queries, database.T)  # (n_q, n_db)
        
        # Broadcast division, single pass
        norms_product = q_norms * db_norms  # (n_q, n_db) via broadcast
        
        # Clamp for numerical stability — fp32 edge cases kill perf
        similarities = np.clip(dots / (norms_product + 1e-8), -1.0, 1.0)
        
        return 1.0 - similarities  # Distance, not similarity
    
    elif metric == "euclidean":
        # Expand (a-b)^2 = a^2 - 2ab + b^2 for vectorization
        q_sq = np.sum(queries * queries, axis=1, keepdims=True)  # (n_q, 1)
        db_sq = np.sum(database * database, axis=1)  # (n_db,)
        
        cross = np.matmul(queries, database.T)  # (n_q, n_db)
        
        # Single allocation, fused broadcast
        dists_sq = q_sq - 2.0 * cross + db_sq  # (n_q, n_db)
        
        # Max with 0 before sqrt — negative from fp error breaks everything
        return np.sqrt(np.maximum(dists_sq, 0.0))
    
    else:
        raise ValueError(f"Unsupported metric: {metric}")


# Warmup function — forces numpy to allocate thread pools, compile paths
def warmup():
    """Call once at module load. Eliminates first-call JIT penalty."""
    dummy_q = np.random.randn(16, 128).astype(np.float32)
    dummy_db = np.random.randn(1000, 128).astype(np.float32)
    distance_batch_optimized(dummy_q, dummy_db, "cosine")
    distance_batch_optimized(dummy_q, dummy_db, "euclidean")

warmup()