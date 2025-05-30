# pages/Page3_Scoring.py
"""
Tab 3 – Scholarship Scoring

Flow:
1. Load preprocessed data and weights (default or custom).
2. Allow user to select scoring methods (SAW, WP, TOPSIS).
3. Compute scores per selected methods.
4. Display and allow CSV download of results.
"""

import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st

# ---------- Constants ----------
BASE_DIR = Path(__file__).parent.parent
PREPROCESSED_FILE = BASE_DIR / "data" / "preprocessed" / "scholarship_sample_preprocessed.csv"
RESULT_DIR = BASE_DIR / "data" / "result"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_WEIGHT_PATH = BASE_DIR / "data" / "weight" / "weight_default.csv"
CUSTOM_WEIGHT_PATH = BASE_DIR / "data" / "weight" / "weight_custom.csv"

# ---------- Helper Functions ----------

def load_preprocessed_data(path: Path) -> Optional[pd.DataFrame]:
    """Load preprocessed scholarship data from CSV."""
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"Preprocessed data file not found at {path}")
        return None

def load_weights(path: Path) -> Optional[pd.DataFrame]:
    """Load weights CSV into DataFrame."""
    try:
        df = pd.read_csv(path)
        if df.empty:
            st.error(f"Weight file at {path} is empty.")
            return None
        return df
    except FileNotFoundError:
        st.error(f"Weight file not found at {path}. Please configure weights first.")
        return None

def save_result(method_name: str, df: pd.DataFrame) -> None:
    """Save scoring result CSV to disk."""
    output_path = RESULT_DIR / f"{method_name.lower()}_result.csv"
    df.to_csv(output_path, index=False)

def compute_saw(features: pd.DataFrame, weights: np.ndarray) -> np.ndarray:
    """Compute SAW scores."""
    norm = features / features.max()
    scores = norm.dot(weights)
    return scores

def compute_wp(features: pd.DataFrame, weights: np.ndarray) -> np.ndarray:
    """Compute WP scores."""
    features_safe = features.replace(0, 1e-6)
    log_matrix = np.log(features_safe) * weights
    scores = np.exp(log_matrix.sum(axis=1))
    return scores

def compute_topsis(features: pd.DataFrame, weights: np.ndarray) -> np.ndarray:
    """Compute TOPSIS scores."""
    norm = features / np.sqrt((features**2).sum())
    weighted = norm * weights

    ideal_pos = weighted.max()
    ideal_neg = weighted.min()

    dist_pos = np.sqrt(((weighted - ideal_pos) ** 2).sum(axis=1))
    dist_neg = np.sqrt(((weighted - ideal_neg) ** 2).sum(axis=1))

    scores = dist_neg / (dist_pos + dist_neg)
    return scores

# ---------- Main Tab Function ----------

def scoring_tab() -> None:
    st.subheader("🎯 Scholarship Scoring")

    # Load data
    df = load_preprocessed_data(PREPROCESSED_FILE)
    if df is None:
        return

    # Select weight file path based on selected mode
    weight_method = st.session_state.get("weight_method", "Default Weights")
    weight_path = CUSTOM_WEIGHT_PATH if weight_method == "Custom Weights" else DEFAULT_WEIGHT_PATH

    # Load weights
    if "weighted_df" in st.session_state:
        weights_df = st.session_state["weighted_df"].copy()
    else:
        weights_df = load_weights(weight_path)
        if weights_df is None:
            return

    weights_dict = weights_df.iloc[0].to_dict()
    criteria = list(weights_dict.keys())
    weights = list(weights_dict.values())


    # Assume all criteria are benefit type
    types = ["Benefit"] * len(criteria)  # currently unused but can be extended

    # Scoring method selection UI
    st.markdown("#### Select Scoring Methods")
    col1, col2, col3 = st.columns(3)
    with col1:
        use_saw = st.checkbox("SAW (Simple Additive Weighting)")
    with col2:
        use_wp = st.checkbox("WP (Weighted Product)")
    with col3:
        use_topsis = st.checkbox("TOPSIS")

    # Compute and display results if any method selected
    if any([use_saw, use_wp, use_topsis]):
        st.markdown("### 📊 Scoring Results")

        # Select feature columns according to criteria from data
        features = df[list(criteria)].copy()

        if use_saw:
            st.markdown("#### 🔹 SAW Result")
            scores = compute_saw(features, weights)
            df_saw = df.copy()
            df_saw["SAW_Score"] = scores
            df_saw = df_saw.sort_values(by="SAW_Score", ascending=False)
            st.dataframe(df_saw[["ID", "SAW_Score"]].reset_index(drop=True), use_container_width=True)
            save_result("SAW", df_saw)
            csv_saw = df_saw.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download SAW Result", csv_saw, "saw_result.csv", "text/csv")

        if use_wp:
            st.markdown("#### 🔹 WP Result")
            scores = compute_wp(features, weights)
            df_wp = df.copy()
            df_wp["WP_Score"] = scores
            df_wp = df_wp.sort_values(by="WP_Score", ascending=False)
            st.dataframe(df_wp[["ID", "WP_Score"]].reset_index(drop=True), use_container_width=True)
            save_result("WP", df_wp)
            csv_wp = df_wp.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download WP Result", csv_wp, "wp_result.csv", "text/csv")

        if use_topsis:
            st.markdown("#### 🔹 TOPSIS Result")
            scores = compute_topsis(features, weights)
            df_topsis = df.copy()
            df_topsis["TOPSIS_Score"] = scores
            df_topsis = df_topsis.sort_values(by="TOPSIS_Score", ascending=False)
            st.dataframe(df_topsis[["ID", "TOPSIS_Score"]].reset_index(drop=True), use_container_width=True)
            save_result("TOPSIS", df_topsis)
            csv_topsis = df_topsis.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download TOPSIS Result", csv_topsis, "topsis_result.csv", "text/csv")

    else:
        st.info("Please select at least one method to calculate scores.")
