"""Tests for walk-forward validation — ensuring no train/test overlap."""

from __future__ import annotations

from packages.models.training import generate_walk_forward_splits


class TestWalkForwardSplits:
    def test_no_train_test_overlap(self) -> None:
        """Train and test sets must never overlap."""
        splits = generate_walk_forward_splits(
            n_samples=2000, train_bars=500, test_bars=100, purge_bars=3, embargo_bars=2
        )

        for split in splits:
            assert split.train_end <= split.test_start, (
                f"Fold {split.fold_idx}: train_end {split.train_end} > test_start {split.test_start}"
            )

    def test_purge_gap_exists(self) -> None:
        """There must be a purge gap between train and test."""
        purge_bars = 5
        splits = generate_walk_forward_splits(
            n_samples=2000, train_bars=500, test_bars=100, purge_bars=purge_bars, embargo_bars=2
        )

        for split in splits:
            gap = split.test_start - split.train_end
            assert gap >= purge_bars, f"Fold {split.fold_idx}: gap {gap} < purge {purge_bars}"

    def test_multiple_folds_generated(self) -> None:
        """Should generate multiple folds for sufficient data."""
        splits = generate_walk_forward_splits(
            n_samples=3000, train_bars=500, test_bars=100, purge_bars=3, embargo_bars=2
        )
        assert len(splits) >= 2

    def test_no_splits_if_insufficient_data(self) -> None:
        """Should return empty list if data is too short."""
        splits = generate_walk_forward_splits(n_samples=100, train_bars=500, test_bars=100)
        assert len(splits) == 0

    def test_folds_are_sequential(self) -> None:
        """Each fold should start after the previous one ends."""
        splits = generate_walk_forward_splits(
            n_samples=5000, train_bars=1000, test_bars=100, purge_bars=3, embargo_bars=2
        )

        for i in range(1, len(splits)):
            prev = splits[i - 1]
            curr = splits[i]
            assert curr.train_start >= prev.test_end, (
                f"Fold {i} starts at {curr.train_start}, but fold {i - 1} ends at {prev.test_end}"
            )

    def test_embargo_between_folds(self) -> None:
        """There should be an embargo gap between consecutive folds."""
        embargo = 5
        splits = generate_walk_forward_splits(
            n_samples=5000, train_bars=1000, test_bars=100, purge_bars=3, embargo_bars=embargo
        )

        for i in range(1, len(splits)):
            gap = splits[i].train_start - splits[i - 1].test_end
            assert gap >= embargo, f"Gap between folds {i - 1} and {i}: {gap} < embargo {embargo}"
