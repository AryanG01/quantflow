"""Uncertainty to confidence mapping.

Converts model prediction uncertainty (IQR from quantile regression)
into a confidence score for position sizing.
"""

from __future__ import annotations

import numpy as np


def uncertainty_to_confidence(
    iqr: float,
    min_iqr: float = 0.2,
    max_iqr: float = 1.5,
) -> float:
    """Map uncertainty (IQR) to confidence score [0, 1].

    Lower IQR → higher confidence (model is more certain).
    Uses linear interpolation clipped to [0, 1].

    Args:
        iqr: Interquartile range (q75 - q25) from quantile predictions
        min_iqr: IQR at which confidence is 1.0 (very certain)
        max_iqr: IQR at which confidence is 0.0 (very uncertain)

    Returns:
        Confidence score in [0, 1]
    """
    if max_iqr <= min_iqr:
        return 0.5

    confidence = 1.0 - (iqr - min_iqr) / (max_iqr - min_iqr)
    return float(np.clip(confidence, 0.0, 1.0))
