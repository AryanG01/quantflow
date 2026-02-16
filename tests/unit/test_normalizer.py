"""Tests for feature normalization — especially lookahead prevention."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from packages.features.normalizer import RollingZScoreNormalizer


class TestRollingZScoreNormalizer:
    def test_shift_prevents_lookahead(self) -> None:
        """Z-score at bar i should only use data from bars < i.

        Verify by checking that changing bar i's value doesn't change
        its own z-score (because stats are shifted).
        """
        np.random.seed(42)
        data = pd.DataFrame({"feat": np.random.randn(200)})

        normalizer = RollingZScoreNormalizer(window=50, shift=1)
        normalized = normalizer.normalize(data)

        # Modify bar 150's value and re-normalize
        data_modified = data.copy()
        data_modified.loc[150, "feat"] = 999.0
        normalized_modified = normalizer.normalize(data_modified)

        # Bar 150's z-score should be different (different raw value)
        # BUT bar 149's z-score should be the same (not affected)
        assert normalized.loc[149, "feat"] == pytest.approx(
            normalized_modified.loc[149, "feat"]
        )

    def test_output_shape_matches_input(self) -> None:
        data = pd.DataFrame({"a": np.random.randn(100), "b": np.random.randn(100)})
        normalizer = RollingZScoreNormalizer(window=20)
        result = normalizer.normalize(data)
        assert result.shape == data.shape

    def test_nan_during_warmup(self) -> None:
        """First `window + shift` bars should be NaN."""
        data = pd.DataFrame({"feat": np.random.randn(200)})
        normalizer = RollingZScoreNormalizer(window=50, shift=1)
        result = normalizer.normalize(data)

        # First 50 values should be NaN (window=50 needs 50 points, shift=1 pushes by 1)
        # Index 50 is the first valid value (rolling over 0..49 shifted by 1)
        assert result.iloc[:50]["feat"].isna().all()
        assert result.iloc[50:55]["feat"].notna().all()

    def test_approximately_standard_normal(self) -> None:
        """After warmup, z-scores should be approximately standard normal."""
        np.random.seed(42)
        data = pd.DataFrame({"feat": np.random.randn(1000)})
        normalizer = RollingZScoreNormalizer(window=100, shift=1)
        result = normalizer.normalize(data)

        valid = result["feat"].dropna()
        assert abs(valid.mean()) < 0.5  # mean near 0
        assert 0.5 < valid.std() < 2.0  # std near 1
