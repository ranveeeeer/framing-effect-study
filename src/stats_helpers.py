"""
Small statistics helpers used by both analysis scripts.
"""

import math

from scipy.stats import fisher_exact


def wilson_ci(successes, n, z=1.96):
    """
    95% confidence interval for a proportion (Wilson method).
    Better than the textbook "p +/- 1.96*SE" when n is small or p is
    near 0% or 100%.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    centre = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    margin = (z / (1 + z**2 / n)) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def compare_frames(risky_gain, n_gain, risky_loss, n_loss):
    """
    Compare % risky in the gain frame with % risky in the loss frame.
    Fisher's exact test asks: if framing made no difference, how likely is
    a gap at least this big by chance? (two-sided p-value)
    """
    table = [[risky_gain, n_gain - risky_gain],
             [risky_loss, n_loss - risky_loss]]
    _, p = fisher_exact(table)
    g_lo, g_hi = wilson_ci(risky_gain, n_gain)
    l_lo, l_hi = wilson_ci(risky_loss, n_loss)
    pct_gain = 100 * risky_gain / n_gain if n_gain else float("nan")
    pct_loss = 100 * risky_loss / n_loss if n_loss else float("nan")
    return {
        "risky_gain": risky_gain, "n_gain": n_gain,
        "pct_gain": round(pct_gain, 1),
        "ci_gain": f"{100*g_lo:.0f}-{100*g_hi:.0f}",
        "risky_loss": risky_loss, "n_loss": n_loss,
        "pct_loss": round(pct_loss, 1),
        "ci_loss": f"{100*l_lo:.0f}-{100*l_hi:.0f}",
        "gap_points": round(pct_loss - pct_gain, 1),
        "fisher_p": round(p, 4),
    }
