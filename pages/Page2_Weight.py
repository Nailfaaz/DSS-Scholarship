import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from typing import Dict, List

# --- Konstanta ---
DEFAULT_WEIGHT_FILE_PATH = "data/weight/weight_default.csv"
CUSTOM_WEIGHT_SAVE_PATH = "data/weight/weight_custom.csv"

CRITERION_DESCRIPTIONS = {
    'C1_GPA': 'Grade Point Average - Academic performance indicator',
    'C2_Certificates': 'Academic certificates and achievements',
    'C3_ParentIncomeIDR': 'Parent income in Indonesian Rupiah (financial need)',
    'C4_Dependents': 'Number of family dependents',
    'C5_OrgScore': 'Organizational involvement score',
    'C6_VolunteerEvents': 'Volunteer activities and community service',
    'C7_LetterScore': 'Recommendation letter quality score',
    'C8_InterviewScore': 'Interview performance score',
    'C9_DocComplete': 'Document completeness score',
    'C10_OnTime': 'Application submission timeliness'
}
CRITERIA_LIST = list(CRITERION_DESCRIPTIONS.keys())
FALLBACK_WEIGHTS = {k: 0.1 for k in CRITERIA_LIST}
RATING_OPTIONS = [1, 2, 3, 4, 5]

# --- Utility Functions ---

def format_label(code: str) -> str:
    return re.sub(r'C\d+_?', '', code).replace('_', ' ')

def validate_weights(weights: Dict[str, float]) -> bool:
    return abs(sum(weights.values()) - 1.0) < 1e-3 if weights else False

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()} if total > 0 else weights

# --- CSV Loading Function ---

def load_weights_from_csv(file_path: str) -> Dict[str, float]:
    if not os.path.exists(file_path):
        st.info(f"File not found: {file_path}. Using fallback weights.")
        return FALLBACK_WEIGHTS

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if df.empty or len(df) == 0:
            st.warning(f"CSV file is empty: {file_path}. Using fallback.")
            return FALLBACK_WEIGHTS

        weights = df.iloc[0].to_dict()
        cleaned_weights = {}

        for criterion in CRITERIA_LIST:
            try:
                cleaned_weights[criterion] = float(weights[criterion])
            except (KeyError, ValueError):
                st.warning(f"Invalid or missing value for {criterion}. Using fallback.")
                return FALLBACK_WEIGHTS

        extras = set(weights.keys()) - set(CRITERIA_LIST)
        if extras:
            st.info(f"Extra columns ignored: {extras}")

        st.success(f"✅ Weights loaded from: {file_path}")
        return cleaned_weights

    except Exception as e:
        st.error(f"Failed to load CSV: {e}. Using fallback weights.")
        return FALLBACK_WEIGHTS

# --- Display Functions ---

def show_weights_table(weights: Dict[str, float], normalized_weights: Dict[str, float], title: str = "Weights"):
    st.markdown(f"### 📊 {title}")
    df = pd.DataFrame([
        {
            "Criterion": crit,
            "Weight": f"{w:.3f}" if w < 1 else str(w),
            "Normalized Weight": f"{normalized_weights.get(crit, 0):.3f}" if normalized_weights else "N/A",
            "Description": CRITERION_DESCRIPTIONS.get(crit, "N/A")
        } for crit, w in weights.items()
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    if normalized_weights:
        if validate_weights(normalized_weights):
            st.success("✅ Weights are normalized (≈ 1.0)")
        else:
            st.warning(f"⚠️ Weights sum = {sum(weights.values()):.3f} ≠ 1.0")
        
def display_action_buttons():
    """Menampilkan tombol aksi lanjutan jika bobot sudah dimuat."""
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("💾 Save Weights as CSV", use_container_width=True, key="save_weights_btn"):
            if "weights" in st.session_state:
                weights_df = pd.DataFrame([st.session_state.custom_normalized_weights])
                weights_df.to_csv(CUSTOM_WEIGHT_SAVE_PATH, index=False)
                st.success(f"✅ Weights saved to {CUSTOM_WEIGHT_SAVE_PATH}")
            else:
                st.warning("⚠️ No weights to save. Please load or input weights first.")
    with col2:
        if st.button("🔄 Normalize Again", use_container_width=True, key="re_normalize_btn"):
            if "weights" in st.session_state:
                st.session_state.custom_normalized_weights = normalize_weights(st.session_state.weights)
                st.success("✅ Weights normalized again.")


# --- Main UI Handlers ---

def default_weights_ui():
    st.info("🔍 Load weights from file or use fallback.")

    path = st.text_input("CSV File Path", value=DEFAULT_WEIGHT_FILE_PATH)
    if st.button("🔄 Load Weights"):
        weights = load_weights_from_csv(path)
        st.session_state["weights"] = weights
        st.session_state["weights_loaded"] = True

    if st.session_state.get("weights_loaded"):
        weights = st.session_state.get("weights", FALLBACK_WEIGHTS)
        is_norm = validate_weights(weights)
        show_weights_table(weights, normalize_weights(weights), title="Default Weights")

def display_custom_weights_config():
    """Menampilkan UI untuk konfigurasi bobot kustom secara manual."""
    st.info("✏️ **Custom Weights Mode**: Atur bobot/rating kriteria secara manual berdasarkan preferensi pengguna atau kebijakan institusi.")
    
    st.markdown("### 🛠️ Custom Weight Configuration")

    custom_weights = {}
    with st.form("custom_weights_form"):
        col1, col2 = st.columns(2)
        with col1:
            for crit in CRITERIA_LIST[:5]:
                selected_value = st.radio(f"**{format_label(crit)}** - {CRITERION_DESCRIPTIONS.get(crit, '')}", RATING_OPTIONS, key=f"rating_{crit}", horizontal=True)
                custom_weights[crit] = selected_value
        
        with col2:
            for crit in CRITERIA_LIST[5:]:
                selected_value = st.radio(f"**{format_label(crit)}** - {CRITERION_DESCRIPTIONS.get(crit, '')}", RATING_OPTIONS, key=f"rating_{crit}", horizontal=True)
                custom_weights[crit] = selected_value

        submitted = st.form_submit_button("✅ Submit Custom Ratings")
        if submitted:
            st.session_state.weights = custom_weights
            st.session_state.custom_normalized_weights = normalize_weights(custom_weights)
            st.success("Custom ratings submitted and normalized!")
    
    if "custom_normalized_weights" in st.session_state:
        show_weights_table(st.session_state.weights, st.session_state.custom_normalized_weights, title="Custom Weights")
        display_action_buttons()

# --- Run ---
def weight_tab():
    """Menampilkan seluruh tab untuk konfigurasi bobot (default & custom)."""
    st.title("🎯 Weight Configuration")
    st.markdown("Atur bobot atau rating masing-masing kriteria yang akan digunakan dalam proses penilaian.")

    st.session_state.weight_method = st.radio(
        "Pilih mode konfigurasi bobot:",
        options=["Default Weights", "Custom Weights"],
        horizontal=True,
        key="weight_mode_radio"
    )

    if st.session_state.weight_method == "Default Weights":
        default_weights_ui()
    elif st.session_state.weight_method == "Custom Weights":
        display_custom_weights_config()
