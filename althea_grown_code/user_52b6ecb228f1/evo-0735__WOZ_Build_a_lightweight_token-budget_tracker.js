// /autonomous-token-budget-tracker
// Woz-style: Every token counts. Make constraint visible.

class TokenBudgetTracker {
  constructor(budget = 200000) {
    this.budget = budget;
    this.spent = 0;
    this.checkpoints = [];
    this.startTime = Date.now();
  }

  consume(tokens, label = 'unlabeled') {
    this.spent += tokens;
    this.checkpoints.push({
      label,
      tokens,
      cumulative: this.spent,
      timestamp: Date.now() - this.startTime
    });
    return this.getStatus();
  }

  getStatus() {
    const remaining = this.budget - this.spent;
    const efficiency = this.spent / (this.checkpoints.length || 1);
    const burnRate = this.spent / ((Date.now() - this.startTime) / 1000 || 1);
    
    return {
      budget: this.budget,
      spent: this.spent,
      remaining,
      utilizationPct: ((this.spent / this.budget) * 100).toFixed(1),
      avgTokensPerOp: efficiency.toFixed(0),
      tokensPerSec: burnRate.toFixed(1),
      checkpoint_count: this.checkpoints.length,
      status: remaining > 0 ? 'ACTIVE' : 'EXCEEDED'
    };
  }

  renderCompact() {
    const s = this.getStatus();
    const bar = this.renderBar(s.utilizationPct);
    return `[TOK ${s.spent}/${s.budget} ${bar} ${s.utilizationPct}% @${s.tokensPerSec}/s]`;
  }

  renderBar(pct, width = 10) {
    const filled = Math.round((pct / 100) * width);
    const empty = width - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  }

  getTopConsumers(n = 5) {
    return this.checkpoints
      .sort((a, b) => b.tokens - a.tokens)
      .slice(0, n)
      .map(cp => `${cp.label}: ${cp.tokens}t`);
  }

  exportMetrics() {
    return {
      summary: this.getStatus(),
      topConsumers: this.getTopConsumers(),
      checkpoints: this.checkpoints
    };
  }
}

// Auto-instantiate global tracker
if (typeof globalThis !== 'undefined') {
  globalThis.ALTHEA_TOKEN_TRACKER = new TokenBudgetTracker(200000);
}

module.exports = TokenBudgetTracker;