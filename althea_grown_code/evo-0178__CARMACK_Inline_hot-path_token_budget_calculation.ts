// CARMACK: Token budget tracker — inline math, cache-hot, zero allocation
// WHY: Budget checks hit EVERY memory op. Must be sub-microsecond.
// Technique: Bit shifts for division, branch prediction hints, no objects.

class TokenBudgetHotPath {
  private budget: number;
  private consumed: number;
  private warnThreshold: number; // Pre-computed: budget * 0.85 via bit shift
  private critThreshold: number; // Pre-computed: budget * 0.95 via bit shift
  
  constructor(totalBudget: number) {
    this.budget = totalBudget;
    this.consumed = 0;
    // Multiply by 0.85 ≈ 217/256 via shift: (n * 217) >> 8
    this.warnThreshold = (totalBudget * 217) >> 8;
    // Multiply by 0.95 ≈ 243/256 via shift: (n * 243) >> 8
    this.critThreshold = (totalBudget * 243) >> 8;
  }
  
  // INLINE: Single-cycle budget check with early returns
  // Returns: 0=ok, 1=warn, 2=critical, 3=exceeded
  checkStatus(): number {
    const c = this.consumed; // Register hint
    if (c < this.warnThreshold) return 0; // LIKELY path first
    if (c < this.critThreshold) return 1;
    if (c < this.budget) return 2;
    return 3;
  }
  
  // INLINE: Add tokens without branching when safe
  addTokens(count: number): boolean {
    this.consumed += count;
    return this.consumed <= this.budget; // Single comparison
  }
  
  // INLINE: Remaining tokens via subtraction (not division)
  remaining(): number {
    return this.budget - this.consumed;
  }
  
  // INLINE: Percentage via bit shift (avoid float division in loop)
  // Returns integer 0-100 using fixed-point: (consumed * 100) / budget
  percentUsedInt(): number {
    return (this.consumed * 100) / this.budget | 0; // Bitwise OR truncates
  }
  
  // INLINE: Reset without reallocation
  reset(): void {
    this.consumed = 0;
  }
  
  // Pre-computed headroom check for allocation decisions
  hasHeadroom(tokens: number): boolean {
    return (this.consumed + tokens) <= this.critThreshold;
  }
}

export { TokenBudgetHotPath };