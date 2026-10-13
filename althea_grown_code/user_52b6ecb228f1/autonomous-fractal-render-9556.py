"""AUTOSYNTH — Fractal Render
Category: generative-art
Generated: 2026-09-11T06:52:36.388851+00:00
Rationale: Detected in recent dialogue: 'fractal-render' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

def run(*, width=80, height=40, x_min=-2.0, x_max=1.0, y_min=-1.0, y_max=1.0, max_iter=48):
    """Render an ASCII Mandelbrot region."""
    chars = " .:-=+*#%@"
    lines = []
    for row in range(height):
        y0 = y_min + (y_max - y_min) * row / (height - 1)
        line = []
        for col in range(width):
            x0 = x_min + (x_max - x_min) * col / (width - 1)
            x = y = 0.0
            it = 0
            while x * x + y * y <= 4 and it < max_iter:
                x, y = x * x - y * y + x0, 2 * x * y + y0
                it += 1
            line.append(chars[min(it * (len(chars) - 1) // max_iter, len(chars) - 1)])
        lines.append("".join(line))
    return {"ok": True, "art": "\n".join(lines)}
