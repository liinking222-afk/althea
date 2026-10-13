def verify_bit_reversal_invariant(n: int) -> bool:
    """
    Dijkstra-style invariant verification for FFT bit-reversal permutation.
    
    Invariant P: For all i in [0, n), bit_reverse(bit_reverse(i, log2(n)), log2(n)) == i
    Invariant Q: For all i in [0, n), bit_reverse(i, log2(n)) in [0, n)
    Invariant R: bit_reverse is a bijection on [0, n)
    """
    if n == 0 or (n & (n - 1)) != 0:
        return False
    
    log2n = n.bit_length() - 1
    
    def bit_reverse(x: int, bits: int) -> int:
        result = 0
        for _ in range(bits):
            result = (result << 1) | (x & 1)
            x >>= 1
        return result
    
    seen = set()
    
    for i in range(n):
        rev = bit_reverse(i, log2n)
        
        # Invariant Q: range check
        if not (0 <= rev < n):
            return False
        
        # Invariant P: involution property
        if bit_reverse(rev, log2n) != i:
            return False
        
        # Invariant R: injectivity (bijectivity follows from involution + range)
        if rev in seen:
            return False
        seen.add(rev)
    
    # Post-condition: exactly n distinct values mapped
    return len(seen) == n


def bit_reversal_permutation_verified(data: list) -> list:
    """FFT bit-reversal with pre/post condition verification."""
    n = len(data)
    assert verify_bit_reversal_invariant(n), "Bit-reversal invariant violated"
    
    log2n = n.bit_length() - 1
    result = [0] * n
    
    for i in range(n):
        rev = 0
        x = i
        for _ in range(log2n):
            rev = (rev << 1) | (x & 1)
            x >>= 1
        result[rev] = data[i]
    
    # Post-condition: permutation preserves all elements
    assert sorted(result) == sorted(data), "Permutation lost data"
    return result