"""Tests for data loader: synthetic generation, sampling, and temporal split."""
import pytest
import os


class TestGenerateSyntheticData:
    """Tests for generate_synthetic_data function."""

    def test_generate_synthetic_data_columns(self, synthetic_df):
        """Synthetic data has all expected columns."""
        expected_columns = [
            "TransactionID", "card_id", "merchant_id", "device_id",
            "TransactionAmt", "TransactionDT", "ProductCD", "addr1",
            "addr2", "DeviceType", "hour_of_day", "isFraud",
        ]
        for col in expected_columns:
            assert col in synthetic_df.columns, f"Missing column: {col}"

    def test_generate_synthetic_data_size(self, synthetic_df):
        """Synthetic data has the requested number of rows."""
        assert len(synthetic_df) == 2000

    def test_generate_synthetic_data_fraud_ratio(self, synthetic_df):
        """Synthetic data has approximately 3.5% fraud rate."""
        fraud_rate = synthetic_df["isFraud"].mean()
        assert 0.01 < fraud_rate < 0.10, f"Fraud rate {fraud_rate:.3f} outside expected range"

    def test_generate_synthetic_data_sorted_timestamps(self, synthetic_df):
        """Synthetic data has sorted TransactionDT values."""
        dt = synthetic_df["TransactionDT"].values
        assert all(dt[i] <= dt[i + 1] for i in range(len(dt) - 1)), "TransactionDT not sorted"

    def test_generate_synthetic_data_shared_devices(self, synthetic_df):
        """Some fraud transactions share device_FRAUD_SHARED device."""
        fraud_rows = synthetic_df[synthetic_df["isFraud"] == 1]
        shared = fraud_rows[fraud_rows["device_id"] == "device_FRAUD_SHARED"]
        assert len(shared) > 0, "No fraud rows with shared device pattern"


class TestGetSample:
    """Tests for get_sample function."""

    def test_get_sample_size(self, synthetic_df):
        """get_sample returns correct number of rows."""
        from backend.data.loader import get_sample
        sample = get_sample(synthetic_df, n=500, fraud_ratio=0.1)
        assert len(sample) == 500

    def test_get_sample_fraud_ratio(self, synthetic_df):
        """get_sample produces approximately the requested fraud ratio."""
        from backend.data.loader import get_sample
        sample = get_sample(synthetic_df, n=500, fraud_ratio=0.1)
        fraud_rate = sample["isFraud"].mean()
        assert 0.05 < fraud_rate < 0.15, f"Sample fraud rate {fraud_rate:.3f} not near 0.1"


class TestTemporalSplit:
    """Tests for load_and_split temporal ordering."""

    def test_temporal_split_sizes(self, sample_train_test):
        """Train has ~80% rows, test has ~20%."""
        train_df, test_df = sample_train_test
        total = len(train_df) + len(test_df)
        train_ratio = len(train_df) / total
        assert 0.75 < train_ratio < 0.85, f"Train ratio {train_ratio:.3f} not near 0.8"

    def test_temporal_split_ordering(self, sample_train_test):
        """All train timestamps < all test timestamps."""
        train_df, test_df = sample_train_test
        assert train_df["TransactionDT"].max() <= test_df["TransactionDT"].min(), \
            "Temporal split violated: some train timestamps >= test timestamps"


class TestLoadIeeeCis:
    """Tests for load_ieee_cis with real data."""

    def test_load_ieee_cis_with_real_data(self):
        """Loads real data if CSVs exist, produces DataFrame with card_id."""
        from backend.data.loader import load_ieee_cis
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
        )
        txn_path = os.path.join(data_dir, "train_transaction.csv")
        if not os.path.exists(txn_path):
            pytest.skip("IEEE-CIS dataset not available")
        df = load_ieee_cis(data_dir)
        assert "card_id" in df.columns
        assert len(df) > 0
