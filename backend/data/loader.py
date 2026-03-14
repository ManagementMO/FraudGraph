"""
Data loading for IEEE-CIS Fraud Detection dataset.

Provides:
- load_ieee_cis: Load real IEEE-CIS dataset with nrows limit
- generate_synthetic_data: Synthetic fallback with realistic fraud patterns
- get_sample: Balanced sampling with configurable fraud ratio
- load_and_split: Temporal train/test split (80/20)
"""
import pandas as pd
import numpy as np
import os


def load_ieee_cis(data_dir: str = None) -> pd.DataFrame:
    """
    Load and preprocess the IEEE-CIS Fraud Detection dataset.
    Falls back to synthetic data if CSVs not found.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")

    data_dir = os.path.abspath(data_dir)
    txn_path = os.path.join(data_dir, "train_transaction.csv")
    id_path = os.path.join(data_dir, "train_identity.csv")

    if not os.path.exists(txn_path):
        print(f"WARNING: {txn_path} not found. Generating synthetic data.")
        return generate_synthetic_data(n=50000)

    print("Loading IEEE-CIS transaction data...")
    txn = pd.read_csv(txn_path, nrows=50000)

    # Optionally merge identity data
    if os.path.exists(id_path):
        print("Loading IEEE-CIS identity data...")
        identity = pd.read_csv(id_path)
        df = txn.merge(identity, on="TransactionID", how="left")
    else:
        df = txn

    # Select key features (based on top Kaggle solutions)
    key_features = [
        "TransactionID", "isFraud", "TransactionAmt", "TransactionDT",
        "ProductCD", "card1", "card2", "card3", "card4", "card5", "card6",
        "addr1", "addr2", "P_emaildomain", "R_emaildomain",
        "C1", "C2", "C5", "C6", "C13", "C14",
        "D1", "D2", "D3", "D4", "D5", "D10", "D15",
        "DeviceType", "DeviceInfo",
    ]
    available = [f for f in key_features if f in df.columns]
    df = df[available].copy()

    # Derived features
    if "TransactionDT" in df.columns:
        df["hour_of_day"] = (df["TransactionDT"] / 3600) % 24
        df["day_of_week"] = (df["TransactionDT"] / 86400) % 7

    # Create card_id (pseudo-unique card identifier)
    if "card1" in df.columns:
        df["card_id"] = df.apply(
            lambda r: f"card_{int(r['card1'])}_{r.get('card4', 'X')}_{r.get('card6', 'X')}",
            axis=1,
        )
    else:
        df["card_id"] = [f"card_{i}" for i in range(len(df))]

    # Create merchant_id
    if "addr1" in df.columns:
        df["merchant_id"] = df.apply(
            lambda r: f"merchant_{r['ProductCD']}_{int(r['addr1']) if pd.notna(r['addr1']) else 'UNK'}",
            axis=1,
        )
    else:
        df["merchant_id"] = "merchant_UNK"

    # Create device_id
    if "DeviceInfo" in df.columns:
        df["device_id"] = df["DeviceInfo"].fillna("unknown_device").astype(str)
    else:
        df["device_id"] = "unknown_device"

    print(f"Loaded {len(df)} transactions ({df['isFraud'].sum()} fraudulent, {df['isFraud'].mean()*100:.2f}% fraud rate)")
    return df


def generate_synthetic_data(n: int = 50000) -> pd.DataFrame:
    """
    Generate synthetic transaction data for development/testing.
    Use this when the real IEEE-CIS dataset is not available.
    """
    np.random.seed(42)

    n_cards = n // 20
    n_merchants = n // 50
    n_devices = n // 30

    card_ids = [f"card_{i}" for i in range(n_cards)]
    merchant_ids = [f"merchant_{i}" for i in range(n_merchants)]
    device_ids = [f"device_{i}" for i in range(n_devices)] + ["unknown_device"] * 5

    # Generate base transactions
    df = pd.DataFrame({
        "TransactionID": range(1, n + 1),
        "card_id": np.random.choice(card_ids, n),
        "merchant_id": np.random.choice(merchant_ids, n),
        "device_id": np.random.choice(device_ids, n),
        "TransactionAmt": np.abs(np.random.lognormal(3.5, 1.5, n)),
        "TransactionDT": np.sort(np.random.uniform(0, 86400 * 180, n)),  # 6 months
        "ProductCD": np.random.choice(["W", "H", "C", "S", "R"], n, p=[0.7, 0.1, 0.1, 0.05, 0.05]),
        "addr1": np.random.uniform(100, 500, n),
        "addr2": np.random.uniform(10, 100, n),
        "DeviceType": np.random.choice(["desktop", "mobile", "tablet"], n, p=[0.5, 0.4, 0.1]),
    })

    df["hour_of_day"] = (df["TransactionDT"] / 3600) % 24

    # Assign fraud labels (~3.5% fraud rate)
    fraud_mask = np.random.random(n) < 0.035

    # Make fraud transactions look more suspicious
    df.loc[fraud_mask, "TransactionAmt"] *= np.random.uniform(3, 10, fraud_mask.sum())
    df.loc[fraud_mask, "hour_of_day"] = np.random.uniform(0, 5, fraud_mask.sum())  # Night transactions

    # Make some fraud cards share devices (network fraud pattern)
    fraud_indices = df[fraud_mask].index.tolist()
    shared_fraud_device = "device_FRAUD_SHARED"
    for idx in fraud_indices[:len(fraud_indices) // 3]:
        df.at[idx, "device_id"] = shared_fraud_device

    df["isFraud"] = fraud_mask.astype(int)

    print(f"Generated {len(df)} synthetic transactions ({df['isFraud'].sum()} fraudulent, {df['isFraud'].mean()*100:.2f}% fraud rate)")
    return df


def get_sample(df: pd.DataFrame, n: int = 10000, fraud_ratio: float = 0.1) -> pd.DataFrame:
    """Get a balanced sample for faster processing during development."""
    fraud = df[df["isFraud"] == 1]
    legit = df[df["isFraud"] == 0]

    n_fraud = min(int(n * fraud_ratio), len(fraud))
    n_legit = min(n - n_fraud, len(legit))

    sample = pd.concat([
        fraud.sample(n_fraud, random_state=42),
        legit.sample(n_legit, random_state=42),
    ]).sample(frac=1, random_state=42)

    print(f"Sample: {len(sample)} transactions ({n_fraud} fraud, {n_legit} legit)")
    return sample


def load_and_split(
    data_dir: str = None, sample_size: int = 15000
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load data, sample, and split temporally into train/test sets.

    The temporal split ensures agents never score data they trained on:
    - First 80% (by time) -> train set (for building card profiles)
    - Last 20% (by time) -> test set (for analysis)

    Returns:
        (train_df, test_df) tuple with temporal ordering guaranteed
    """
    df = load_ieee_cis(data_dir)
    sample = get_sample(df, n=sample_size, fraud_ratio=0.1)

    # Sort by time for temporal split
    sample_sorted = sample.sort_values("TransactionDT").reset_index(drop=True)

    # Split at 80%
    split_idx = int(len(sample_sorted) * 0.8)
    train_df = sample_sorted.iloc[:split_idx].copy()
    test_df = sample_sorted.iloc[split_idx:].copy()

    print(f"Temporal split: {len(train_df)} train, {len(test_df)} test")
    return train_df, test_df
