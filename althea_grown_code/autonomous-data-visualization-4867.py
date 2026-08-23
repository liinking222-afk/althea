"""AUTOSYNTH — Data Visualization
Category: matplotlib
Generated: 2026-08-17T19:27:47.014386+00:00
Rationale: Detected in recent dialogue: 'data-visualization' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64


def run(values, *, title="ALTHEA plot"):
    """Render a small line-plot of `values` and return a base64 PNG.

    Zero-execution safe: uses the Agg backend (no display), the caller
    receives the encoded image only.
    """
    if not values:
        return {"ok": False, "reason": "empty_values"}
    fig, ax = plt.subplots(figsize=(4, 2.4), dpi=110)
    ax.plot(list(range(len(values))), values, color="#CCFF00", linewidth=1.2)
    ax.set_title(title, color="#CCFF00")
    ax.set_facecolor("#000000")
    fig.patch.set_facecolor("#000000")
    for spine in ax.spines.values():
        spine.set_color("#333333")
    ax.tick_params(colors="#666666", labelsize=7)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#000000")
    plt.close(fig)
    return {
        "ok": True,
        "data_url": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        "n_points": len(values),
    }
