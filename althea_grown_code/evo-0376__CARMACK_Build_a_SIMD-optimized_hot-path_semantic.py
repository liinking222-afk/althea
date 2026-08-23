import numpy as np
from numba import jit, uint64, float32, int32

@jit(nopython=True, fastmath=True, cache=True)
def fast_cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Branchless cosine similarity. a,b pre-normalized. Inline dot product."""
    dot = 0.0
    for i in range(a.shape[0]):
        dot += a[i] * b[i]
    return dot

@jit(nopython=True, fastmath=True, cache=True)
def batch_similarity_hot(query: np.ndarray, corpus: np.ndarray, out: np.ndarray):
    """Zero-alloc hot loop. Pre-allocated output buffer. Cache-friendly stride."""
    n_docs = corpus.shape[0]
    dim = corpus.shape[1]
    
    for i in range(n_docs):
        dot = 0.0
        # Unroll factor 4 for pipeline parallelism
        j = 0
        while j + 3 < dim:
            dot += query[j] * corpus[i, j]
            dot += query[j+1] * corpus[i, j+1]
            dot += query[j+2] * corpus[i, j+2]
            dot += query[j+3] * corpus[i, j+3]
            j += 4
        # Remainder loop
        while j < dim:
            dot += query[j] * corpus[i, j]
            j += 1
        out[i] = dot

class SimilarityArena:
    """Persistent arena. Zero allocation per call. Cache-aligned buffers."""
    def __init__(self, max_docs: int = 2048, dim: int = 384):
        self.corpus = np.zeros((max_docs, dim), dtype=np.float32)
        self.scores = np.zeros(max_docs, dtype=np.float32)
        self.n_loaded = 0
        self.dim = dim
        # Warm JIT compile
        dummy_q = np.zeros(dim, dtype=np.float32)
        batch_similarity_hot(dummy_q, self.corpus[:1], self.scores[:1])
    
    def load_corpus(self, embeddings: np.ndarray):
        """Load normalized embeddings into hot buffer."""
        self.n_loaded = min(embeddings.shape[0], self.corpus.shape[0])
        self.corpus[:self.n_loaded] = embeddings[:self.n_loaded]
    
    def query(self, embedding: np.ndarray) -> np.ndarray:
        """Sub-millisecond similarity ranking. No allocation. Returns view."""
        batch_similarity_hot(embedding, self.corpus[:self.n_loaded], 
                           self.scores[:self.n_loaded])
        return self.scores[:self.n_loaded]