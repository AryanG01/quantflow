"""Population Stability Index (PSI) for feature drift detection."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt


def compute_psi(
    reference: npt.NDArray[np.float64],
    current: npt.NDArray[np.float64],
    n_bins: int = 10,
) -> float:
    """Compute Population Stability Index between two distributions.

    PSI < 0.1: no significant shift
    PSI 0.1-0.2: moderate shift
    PSI > 0.2: significant shift (alert)

    Args:
        reference: Reference distribution (training data)
        current: Current distribution (recent data)
        n_bins: Number of bins for discretization

    Returns:
        PSI value
    """
    # Create bins from reference distribution
    edges = np.percentile(reference, np.linspace(0, 100, n_bins + 1))
    edges[0] = -np.inf
    edges[-1] = np.inf

    ref_counts = np.histogram(reference, bins=edges)[0].astype(np.float64)
    cur_counts = np.histogram(current, bins=edges)[0].astype(np.float64)

    # Normalize to proportions
    ref_pct = ref_counts / ref_counts.sum()
    cur_pct = cur_counts / cur_counts.sum()

    # Replace zeros to avoid log(0)
    ref_pct = np.clip(ref_pct, 1e-6, None)
    cur_pct = np.clip(cur_pct, 1e-6, None)

    psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
    return psi
