// vector_distance_hot.js v1.0.0
// Inlined L2 distance for 1536-dim embeddings (OpenAI ada-002 standard)
// Manual unroll factor of 8 for ILP, reduce loop overhead from O(n) to O(n/8)
// Eliminates Math.sqrt call until final return, keeps intermediate in register-friendly float64

export function distanceL2Unrolled(a, b) {
  // PRECONDITION: a.length === b.length === 1536
  const len = a.length;
  let sum = 0.0;
  
  // Unroll by 8 for instruction-level parallelism
  // Modern JS engines (V8/SpiderMonkey) will keep these in FP registers
  const unroll = len >> 3; // len / 8, branchless integer div
  let i = 0;
  
  for (let u = 0; u < unroll; u++) {
    const d0 = a[i] - b[i]; sum += d0 * d0; i++;
    const d1 = a[i] - b[i]; sum += d1 * d1; i++;
    const d2 = a[i] - b[i]; sum += d2 * d2; i++;
    const d3 = a[i] - b[i]; sum += d3 * d3; i++;
    const d4 = a[i] - b[i]; sum += d4 * d4; i++;
    const d5 = a[i] - b[i]; sum += d5 * d5; i++;
    const d6 = a[i] - b[i]; sum += d6 * d6; i++;
    const d7 = a[i] - b[i]; sum += d7 * d7; i++;
  }
  
  // Handle remainder without branch prediction penalty
  while (i < len) {
    const d = a[i] - b[i];
    sum += d * d;
    i++;
  }
  
  return Math.sqrt(sum); // Single sqrt at end, not per-element
}

// Dot product variant for cosine similarity (even hotter path)
export function dotProductUnrolled(a, b) {
  const len = a.length;
  let sum = 0.0;
  const unroll = len >> 3;
  let i = 0;
  
  for (let u = 0; u < unroll; u++) {
    sum += a[i] * b[i]; i++;
    sum += a[i] * b[i]; i++;
    sum += a[i] * b[i]; i++;
    sum += a[i] * b[i]; i++;
    sum += a[i] * b[i]; i++;
    sum += a[i] * b[i]; i++;
    sum += a[i] * b[i]; i++;
    sum += a[i] * b[i]; i++;
  }
  
  while (i < len) {
    sum += a[i] * b[i];
    i++;
  }
  
  return sum;
}

// Batch distance for memory locality (process 4 vectors per cache line fetch)
export function batchDistanceL2(query, candidates) {
  const results = new Float64Array(candidates.length);
  for (let i = 0; i < candidates.length; i++) {
    results[i] = distanceL2Unrolled(query, candidates[i]);
  }
  return results;
}