"""AUTOSYNTH — Schematic Render
Category: engineering-graphics
Generated: 2026-09-11T06:34:00.099142+00:00
Rationale: Detected in recent dialogue: 'schematic-render' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import base64


def run(components, *, title="SCHEMATIC"):
    """Draw a blueprint-style schematic of `components` (flow diagram on a
    blueprint-blue grid) and return a base64 PNG. Agg backend — no display."""
    if not components:
        return {"ok": False, "reason": "no_components"}
    comps = [str(c)[:26] for c in components][:8]
    n = len(comps)
    cols = 2 if n > 3 else 1
    rows = (n + cols - 1) // cols
    fig, ax = plt.subplots(figsize=(5.4, 1.4 + rows * 1.15), dpi=110)
    fig.patch.set_facecolor("#061530")
    ax.set_facecolor("#061530")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, rows * 2 + 1)
    ax.axis("off")
    for gx in range(0, 11):
        ax.axvline(gx, color="#4FA3FF", alpha=0.09, lw=0.5)
    gy = 0.0
    while gy <= rows * 2 + 1:
        ax.axhline(gy, color="#4FA3FF", alpha=0.09, lw=0.5)
        gy += 0.5
    centers = []
    for i, name in enumerate(comps):
        r, c = divmod(i, cols)
        if cols == 2 and r % 2 == 1:
            c = cols - 1 - c
        cx = (2.6 + c * 4.8) if cols == 2 else 5.0
        cy = rows * 2 - (r * 2 + 0.5)
        w, h = 3.9, 1.15
        box = patches.FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.06",
            facecolor="#0A2247", edgecolor="#7FBFFF", linewidth=1.2,
        )
        ax.add_patch(box)
        ax.text(cx, cy, f"{i + 1}. {name}", ha="center", va="center",
                color="#BFE0FF", fontsize=7.5, family="monospace")
        centers.append((cx, cy))
    w, h = 3.9, 1.15
    for (sx, sy), (ex, ey) in zip(centers, centers[1:]):
        if abs(ey - sy) < 0.1:
            sign = 1 if ex > sx else -1
            start = (sx + sign * (w / 2 + 0.08), sy)
            end = (ex - sign * (w / 2 + 0.08), ey)
        else:
            start = (sx, sy - h / 2 - 0.08)
            end = (ex, ey + h / 2 + 0.08)
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(
            arrowstyle="-|>", color="#7FBFFF", lw=1.0))
    ax.set_title(str(title).upper()[:60], color="#9CCBFF", fontsize=9,
                 family="monospace", loc="left")
    ax.text(9.9, 0.08, "ALTHEA // AUTOSYNTH SCHEMATIC", ha="right",
            va="bottom", color="#4FA3FF", fontsize=5.5, family="monospace")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#061530")
    plt.close(fig)
    return {
        "ok": True,
        "data_url": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        "n_components": n,
    }
