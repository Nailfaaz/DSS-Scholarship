# pages/Page2_WeightConfig.py
"""
Tab 2 – Weight Configuration

Flow:
1. Load default weights from CSV or fallback to predefined.
2. Show loaded weights with normalized values and descriptions.
3. Allow manual custom weight input via form.
4. Normalize custom weights and save option.
"""

import os
import re
from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st

# ---------- Constants ----------
BASE_DIR = Path(__file__).parent.parent
DEFAULT_WEIGHT_PATH = BASE_DIR / "data" / "weight" / "weight_default.csv"
CUSTOM_WEIGHT_SAVE_PATH = BASE_DIR / "data" / "weight" / "weight_custom.csv"

CRITERION_DESCRIPTIONS: Dict[str, str] = {
    "C1_GPA": "Grade Point Average - Academic performance indicator",
    "C2_Certificates": "Academic certificates and achievements",
    "C3_ParentIncomeIDR": "Parent income in Indonesian Rupiah (financial need)",
    "C4_Dependents": "Number of family dependents",
    "C5_OrgScore": "Organizational involvement score",
    "C6_VolunteerEvents": "Volunteer activities and community service",
    "C7_LetterScore": "Recommendation letter quality score",
    "C8_InterviewScore": "Interview performance score",
    "C9_DocComplete": "Document completeness score",
    "C10_OnTime": "Application submission timeliness",
}

CRITERIA_LIST = list(CRITERION_DESCRIPTIONS.keys())
FALLBACK_WEIGHTS: Dict[str, float] = {k: 0.1 for k in CRITERIA_LIST}
RATING_OPTIONS = [1, 2, 3, 4, 5]

# ---------- Helper Functions ----------

def format_label(code: str) -> str:
    """
    Convert criterion code to human-readable label.
    Example: 'C1_GPA' -> 'GPA'
    """
    label = re.sub(r"C\d+_?", "", code).replace("_", " ")
    return label.strip()

def validate_weights(weights: Dict[str, float]) -> bool:
    """Validate that sum of weights is approximately 1.0."""
    if not weights:
        return False
    return abs(sum(weights.values()) - 1.0) < 1e-3

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize weights so their sum equals 1."""
    total = sum(weights.values())
    if total > 0:
        return {k: v / total for k, v in weights.items()}
    return weights

def load_weights_from_csv(filepath: Path) -> Dict[str, float]:
    """Load weights from CSV file, fallback if not found or invalid."""
    if not filepath.exists():
        st.info(f"File not found: {filepath}. Using fallback weights.")
        return FALLBACK_WEIGHTS

    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig")
        if df.empty:
            st.warning(f"CSV file is empty: {filepath}. Using fallback weights.")
            return FALLBACK_WEIGHTS

        weights_row = df.iloc[0].to_dict()
        weights: Dict[str, float] = {}

        for crit in CRITERIA_LIST:
            try:
                weights[crit] = float(weights_row[crit])
            except (KeyError, ValueError):
                st.warning(f"Invalid or missing weight for {crit}. Using fallback weights.")
                return FALLBACK_WEIGHTS

        extras = set(weights_row.keys()) - set(CRITERIA_LIST)
        if extras:
            st.info(f"Ignored extra columns: {extras}")

        st.success(f"✅ Weights loaded from {filepath}")
        return weights

    except Exception as e:
        st.error(f"Failed to load CSV: {e}. Using fallback weights.")
        return FALLBACK_WEIGHTS

def show_weights_table(weights: Dict[str, float], normalized: Dict[str, float], title: str = "Weights") -> None:
    """Display weights with normalized values and descriptions in a table."""
    st.markdown(f"### 📊 {title}")
    data = [
        {
            "Criterion": crit,
            "Weight": f"{weights[crit]:.3f}" if weights[crit] < 1 else str(weights[crit]),
            "Normalized Weight": f"{normalized.get(crit, 0):.3f}" if normalized else "N/A",
            "Description": CRITERION_DESCRIPTIONS.get(crit, "N/A"),
        }
        for crit in CRITERIA_LIST
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if normalized:
        if validate_weights(normalized):
            st.success("✅ Weights are normalized (≈ 1.0)")
        else:
            st.warning(f"⚠️ Sum of weights = {sum(weights.values()):.3f} ≠ 1.0")

def display_action_buttons() -> None:
    """Display save and re-normalize buttons if weights loaded."""
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Weights as CSV", use_container_width=True, key="save_weights_btn"):
            if "weights" in st.session_state and "custom_normalized_weights" in st.session_state:
                weights_df = pd.DataFrame([st.session_state["custom_normalized_weights"]])
                weights_df.to_csv(CUSTOM_WEIGHT_SAVE_PATH, index=False)
                st.success(f"✅ Weights saved to {CUSTOM_WEIGHT_SAVE_PATH}")
            else:
                st.warning("⚠️ No weights to save. Load or input weights first.")

    with col2:
        if st.button("🔄 Normalize Again", use_container_width=True, key="re_normalize_btn"):
            if "weights" in st.session_state:
                st.session_state["custom_normalized_weights"] = normalize_weights(st.session_state["weights"])
                st.success("✅ Weights normalized again.")

# ---------- UI Functions ----------

def default_weights_ui() -> None:
    """UI for loading and displaying default weights from CSV file."""
    st.info("🔍 Load weights from file or fallback to default weights.")

    path_input = st.text_input("CSV File Path", value=str(DEFAULT_WEIGHT_PATH))
    if st.button("🔄 Load Weights"):
        weights = load_weights_from_csv(Path(path_input))
        st.session_state["weights"] = weights
        st.session_state["weights_loaded"] = True

    if st.session_state.get("weights_loaded"):
        weights = st.session_state.get("weights", FALLBACK_WEIGHTS)
        normalized = normalize_weights(weights)
        show_weights_table(weights, normalized, title="Default Weights")

def custom_weights_ui() -> None:
    """UI for manual custom weight configuration."""
    st.info("✏️ **Custom Weights Mode**: Set weights manually.")

    st.markdown("### 🛠️ Custom Weight Configuration")

    custom_weights: Dict[str, int] = {}

    with st.form("custom_weights_form"):
        col1, col2 = st.columns(2)

        for crit in CRITERIA_LIST[:5]:
            custom_weights[crit] = st.radio(
                f"**{format_label(crit)}** - {CRITERION_DESCRIPTIONS.get(crit, '')}",
                RATING_OPTIONS,
                key=f"rating_{crit}",
                horizontal=True,
            )

        for crit in CRITERIA_LIST[5:]:
            custom_weights[crit] = st.radio(
                f"**{format_label(crit)}** - {CRITERION_DESCRIPTIONS.get(crit, '')}",
                RATING_OPTIONS,
                key=f"rating_{crit}",
                horizontal=True,
            )

        submitted = st.form_submit_button("✅ Submit Custom Ratings")
        if submitted:
            st.session_state["weights"] = custom_weights
            st.session_state["custom_normalized_weights"] = normalize_weights(custom_weights)
            st.success("Custom ratings submitted and normalized!")

    if "custom_normalized_weights" in st.session_state:
        show_weights_table(
            st.session_state["weights"],
            st.session_state["custom_normalized_weights"],
            title="Custom Weights",
        )
        display_action_buttons()

# ---------- Main Tab Function ----------

def weight_tab() -> None:
    """Main weight configuration tab."""
    st.title("🎯 Weight Configuration")
    st.markdown("Set or adjust the weight or rating for each criterion used in the evaluation.")

    st.session_state["weight_method"] = st.radio(
        "Choose weight configuration mode:",
        options=["Default Weights", "Custom Weights"],
        horizontal=True,
        key="weight_mode_radio",
    )

    if st.session_state["weight_method"] == "Default Weights":
        default_weights_ui()
    else:
        custom_weights_ui()
