"""Walk-forward training with purged k-fold validation.

Ensures strict temporal separation between train and test sets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from packages.common.logging import get_logger

if TYPE_CHECKING:
    import pandas as pd

    from packages.models.interfaces import ModelPredictor

logger = get_logger(__name__)


@dataclass
class WalkForwardSplit:
    """A single train/test split in walk-forward validation."""

    train_start: int
    train_end: int
    test_start: int
    test_end: int
    fold_idx: int


@dataclass
class WalkForwardResult:
    """Results from one fold of walk-forward validation."""

    fold_idx: int
    train_metrics: dict[str, float]
    test_predictions: npt.NDArray[np.int64]
    test_labels: npt.NDArray[np.int64]
    test_accuracy: float


def generate_walk_forward_splits(
    n_samples: int,
    train_bars: int = 1000,
    test_bars: int = 100,
    purge_bars: int = 3,
    embargo_bars: int = 2,
) -> list[WalkForwardSplit]:
    """Generate walk-forward train/test splits.

    Layout per fold:
    [----train----][purge][----test----][embargo]
                                                [----train----][purge][----test----]...

    Args:
        n_samples: Total number of bars
        train_bars: Training window size
        test_bars: Test window size
        purge_bars: Gap between train and test (prevent label leakage)
        embargo_bars: Gap after test before next train starts

    Returns:
        List of WalkForwardSplit objects
    """
    splits = []
    fold_idx = 0
    start = 0

    while True:
        train_start = start
        train_end = train_start + train_bars

        test_start = train_end + purge_bars
        test_end = test_start + test_bars

        if test_end > n_samples:
            break

        splits.append(
            WalkForwardSplit(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                fold_idx=fold_idx,
            )
        )

        fold_idx += 1
        start = test_end + embargo_bars

    return splits


def run_walk_forward(
    model: ModelPredictor,
    X: pd.DataFrame,
    y: npt.NDArray[np.int64],
    train_bars: int = 1000,
    test_bars: int = 100,
    purge_bars: int = 3,
    embargo_bars: int = 2,
) -> list[WalkForwardResult]:
    """Run walk-forward validation.

    For each fold:
    1. Train model on training window
    2. Predict on test window
    3. Record accuracy

    Args:
        model: ModelPredictor instance (will be retrained each fold)
        X: Feature DataFrame
        y: Label array
        train_bars, test_bars, purge_bars, embargo_bars: Split parameters

    Returns:
        List of WalkForwardResult for each fold
    """
    splits = generate_walk_forward_splits(
        n_samples=len(X),
        train_bars=train_bars,
        test_bars=test_bars,
        purge_bars=purge_bars,
        embargo_bars=embargo_bars,
    )

    if not splits:
        logger.warning("no_walk_forward_splits", n_samples=len(X), train_bars=train_bars)
        return []

    results = []
    for split in splits:
        X_train = X.iloc[split.train_start : split.train_end]
        y_train = y[split.train_start : split.train_end]
        X_test = X.iloc[split.test_start : split.test_end]
        y_test = y[split.test_start : split.test_end]

        # Filter out unlabeled samples (label == -1)
        valid_train = y_train >= 0
        valid_test = y_test >= 0

        if valid_train.sum() < 50:  # minimum training samples
            logger.warning("insufficient_training_data", fold=split.fold_idx)
            continue

        train_metrics = model.train(X_train[valid_train], y_train[valid_train])

        predictions = model.predict(X_test[valid_test])
        pred_labels = np.array([p.label for p in predictions], dtype=np.int64)
        actual_labels = y_test[valid_test]

        accuracy = float(np.mean(pred_labels == actual_labels)) if len(actual_labels) > 0 else 0.0

        results.append(
            WalkForwardResult(
                fold_idx=split.fold_idx,
                train_metrics=train_metrics,
                test_predictions=pred_labels,
                test_labels=actual_labels,
                test_accuracy=accuracy,
            )
        )

        logger.info(
            "walk_forward_fold",
            fold=split.fold_idx,
            train_size=int(valid_train.sum()),
            test_size=int(valid_test.sum()),
            accuracy=round(accuracy, 4),
        )

    return results
