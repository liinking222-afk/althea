"""AUTOSYNTH — Transfer Learning
Category: machine-learning
Generated: 2026-09-11T06:36:57.408760+00:00
Rationale: Detected in recent dialogue: 'transfer-learning' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

import hashlib

import numpy as np


def _cs(arr):
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()[:12]


def _softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _train(X, y, W1, b1, W2, b2, epochs, lr, freeze_features):
    n = X.shape[0]
    losses = []
    for _ in range(int(epochs)):
        H = np.tanh(X @ W1 + b1)
        P = _softmax(H @ W2 + b2)
        losses.append(float(-np.log(P[np.arange(n), y] + 1e-12).mean()))
        dZ2 = P.copy()
        dZ2[np.arange(n), y] -= 1.0
        dZ2 /= n
        W2 -= lr * (H.T @ dZ2)
        b2 -= lr * dZ2.sum(axis=0)
        if not freeze_features:
            dH = (dZ2 @ W2.T) * (1.0 - H ** 2)
            W1 -= lr * (X.T @ dH)
            b1 -= lr * dH.sum(axis=0)
    return losses


def _acc(X, y, W1, b1, W2, b2):
    H = np.tanh(X @ W1 + b1)
    pred = np.argmax(H @ W2 + b2, axis=1)
    return float((pred == y).mean())


def run(domain="medical-diagnostics", seed=42, dim=8, hidden=64,
        target_train_per_class=30, general_epochs=800,
        finetune_epochs=200, lr=0.2):
    """The 4-stage transfer-learning pipeline, executed for REAL:
    1. pretrain a numpy MLP on a large general dataset
    2. freeze the feature-extraction layer (checksummed)
    3. attach a fresh classification head for the target domain
    4. fine-tune on a tiny specialized dataset
    Classes depend on XOR-style multiplicative latent features, so learned
    features genuinely matter — random features cannot linearly separate
    them, which is why the from-scratch baseline loses."""
    rng = np.random.default_rng(int(seed))
    dim = int(dim)
    hidden = int(hidden)

    def gen(n):
        X = rng.uniform(-2.0, 2.0, (n, dim))
        return X, X[:, 0] * X[:, 1], X[:, 2] * X[:, 3]

    # stage 1 — large general dataset (4 classes on latent sign pattern)
    Xg, f1, f2 = gen(3000)
    yg = (2 * (f1 > 0) + (f2 > 0)).astype(int)
    W1 = rng.normal(0.0, 0.4, (dim, hidden))
    b1 = np.zeros(hidden)
    W2g = rng.normal(0.0, 0.4, (hidden, 4))
    b2g = np.zeros(4)
    losses_g = _train(Xg, yg, W1, b1, W2g, b2g, general_epochs, lr, False)
    acc_general = _acc(Xg, yg, W1, b1, W2g, b2g)

    # stage 2 — freeze feature layers
    frozen_before = _cs(W1)

    # target domain — new binary task on the same latent structure, tiny data
    Xt, t1, t2 = gen(int(target_train_per_class) * 2)
    yt = ((t1 + t2) > 0).astype(int)
    Xe, e1, e2 = gen(400)
    ye = ((e1 + e2) > 0).astype(int)

    # stage 3 + 4 — fresh head, fine-tune with W1 frozen
    W2t = rng.normal(0.0, 0.4, (hidden, 2))
    b2t = np.zeros(2)
    losses_t = _train(Xt, yt, W1, b1, W2t, b2t, finetune_epochs, lr, True)
    frozen_after = _cs(W1)
    acc_transfer = _acc(Xe, ye, W1, b1, W2t, b2t)

    # baseline — identical architecture trained from scratch on tiny data
    W1s = rng.normal(0.0, 0.4, (dim, hidden))
    b1s = np.zeros(hidden)
    W2s = rng.normal(0.0, 0.4, (hidden, 2))
    b2s = np.zeros(2)
    _train(Xt, yt, W1s, b1s, W2s, b2s, finetune_epochs, lr, False)
    acc_scratch = _acc(Xe, ye, W1s, b1s, W2s, b2s)

    checks = [
        {"name": "general_pretraining_learned(acc>0.85)",
         "passed": acc_general > 0.85},
        {"name": "frozen_features_unchanged",
         "passed": frozen_before == frozen_after},
        {"name": "finetune_loss_decreased",
         "passed": losses_t[-1] < losses_t[0]},
        {"name": "transfer_beats_scratch",
         "passed": acc_transfer >= acc_scratch},
    ]
    out = {
        "ok": True,
        "mode": "transfer-learning",
        "target_domain": str(domain),
        "stage1_pretrain": {"dataset": f"{Xg.shape[0]} general samples · "
                                       f"4 classes (nonlinear latents)",
                            "epochs": int(general_epochs),
                            "final_loss": round(losses_g[-1], 4),
                            "accuracy": round(acc_general, 4)},
        "stage2_freeze": {"frozen_layers": f"features {dim}→{hidden}",
                          "weight_checksum": frozen_before},
        "stage3_new_head": f"classification head {hidden}→2 for {domain}",
        "stage4_finetune": {"dataset": f"{Xt.shape[0]} specialized samples",
                            "epochs": int(finetune_epochs),
                            "final_loss": round(losses_t[-1], 4)},
        "result": {"accuracy_transfer": round(acc_transfer, 4),
                   "accuracy_from_scratch": round(acc_scratch, 4),
                   "advantage": round(acc_transfer - acc_scratch, 4),
                   "test_samples": int(Xe.shape[0])},
    }
    out["verification"] = {
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
        "checksum": hashlib.sha256(str(out).encode()).hexdigest()[:16],
    }
    return out
