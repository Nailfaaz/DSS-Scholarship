# pages/Page1_Upload.py
"""
Tab 1 – Upload / Choose Data

Flow:
1. Offer a downloadable CSV template (data/template/template.csv).
2. Let the user:
    • pick an existing CSV in data/input/, or
    • upload their own CSV.
3. Validate schema + NaNs.
4. Pre-process C3_ParentIncomeIDR → 1-to-5 band score.
5. Save:
    • original file (if uploaded) → data/input/
    • pre-processed file → data/preprocessed/{name}_preprocessed.csv
6. Store DataFrame in st.session_state.df and preview it.
"""

import os
from pathlib import Path
import pandas as pd
import streamlit as st

# Directories setup relative to this script
HERE = Path(__file__).parent
BASE_DIR = HERE.parent

INPUT_DIR = BASE_DIR / "data" / "input"
PREPROC_DIR = BASE_DIR / "data" / "preprocessed"
TEMPLATE_DIR = BASE_DIR / "data" / "template"
TEMPLATE_PATH = TEMPLATE_DIR / "template.csv"

# Ensure required directories exist
for directory in [INPUT_DIR, PREPROC_DIR, TEMPLATE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Expected CSV columns
EXPECTED_COLUMNS = [
    "ID", "C1_GPA", "C2_Certificates", "C3_ParentIncomeIDR",
    "C4_Dependents", "C5_OrgScore", "C6_VolunteerEvents",
    "C7_LetterScore", "C8_InterviewScore", "C9_DocComplete", "C10_OnTime"
]

def map_income_to_score(idr: float) -> int:
    """
    Map Indonesian Rupiah income value to a score band:
    - <4M   : 4
    - 4-6M  : 5
    - 6-10M : 3
    - 10-20M: 2
    - >=20M : 1
    """
    if idr < 4_000_000:
        return 4
    elif idr < 6_000_000:
        return 5
    elif idr < 10_000_000:
        return 3
    elif idr < 20_000_000:
        return 2
    return 1

def load_dataframe_from_uploaded(uploaded_file) -> pd.DataFrame:
    """Load CSV from uploaded file object."""
    try:
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"❌ Unable to read uploaded file: {e}")
        return None

def load_dataframe_from_file(filepath: Path) -> pd.DataFrame:
    """Load CSV from file path."""
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        st.error(f"❌ Unable to read file {filepath.name}: {e}")
        return None

def validate_dataframe(df: pd.DataFrame) -> bool:
    """Check if dataframe has required columns and no missing values."""
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        return False

    nan_cols = df.columns[df.isnull().any()].tolist()
    if nan_cols:
        st.error(f"❌ Dataset contains missing values in columns: {', '.join(nan_cols)}")
        return False

    return True

def preprocess_income_column(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess C3_ParentIncomeIDR column to income score bands."""
    try:
        df["C3_ParentIncomeIDR"] = (
            df["C3_ParentIncomeIDR"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True)
            .astype(float)
            .apply(map_income_to_score)
        )
        return df
    except Exception as e:
        st.error(f"❌ Failed to preprocess C3_ParentIncomeIDR column: {e}")
        return None

def save_uploaded_file(uploaded_file, save_dir: Path) -> None:
    """Save uploaded file to disk."""
    uploaded_file.seek(0)
    with open(save_dir / uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

def upload_tab() -> None:
    st.header("1 . Upload / Choose Data")

    # Downloadable CSV template
    with st.expander("📄 Download CSV template", expanded=True):
        if TEMPLATE_PATH.exists():
            with open(TEMPLATE_PATH, "rb") as f:
                st.download_button(
                    label="⬇️  Save template",
                    data=f.read(),
                    file_name="scholarship_template.csv",
                    mime="text/csv",
                )
        else:
            st.error(f"Template file not found: {TEMPLATE_PATH}")

    st.markdown("---")

    # List existing datasets
    existing_files = sorted([p.name for p in INPUT_DIR.glob("*.csv")])
    existing_files = ["-- Select --"] + existing_files
    selected_file = st.selectbox("Choose a dataset in *data/input/*:", existing_files)

    # File uploader widget
    uploaded_file = st.file_uploader("Or upload a new CSV", type=["csv"])

    df = None
    src_name = None
    is_uploaded = False

    # Determine data source and load DataFrame
    if uploaded_file is not None:
        src_name = uploaded_file.name
        is_uploaded = True
        df = load_dataframe_from_uploaded(uploaded_file)
        if df is None:
            return
    elif selected_file != "-- Select --":
        src_name = selected_file
        df = load_dataframe_from_file(INPUT_DIR / selected_file)
        if df is None:
            return
    else:
        st.info("📂 Please select an existing dataset or upload a new one.")
        return

    # Validate dataframe columns and missing values
    if not validate_dataframe(df):
        return

    # Preprocess income column
    df_processed = preprocess_income_column(df)
    if df_processed is None:
        return

    # Save preprocessed data
    preproc_filename = f"{Path(src_name).stem}_preprocessed.csv"
    df_processed.to_csv(PREPROC_DIR / preproc_filename, index=False)

    # Save original uploaded file if applicable
    if is_uploaded:
        save_uploaded_file(uploaded_file, INPUT_DIR)

    st.success(
        f"✅ Pre-processed data saved as **{preproc_filename}** in *data/preprocessed/*. Ready for next step."
    )

    # Store DataFrame in session state and display preview
    st.session_state.df = df_processed
    st.subheader("Preview of Pre-processed Data")
    st.dataframe(df_processed, use_container_width=True)
    st.markdown(f"**Rows:** {df_processed.shape[0]} &nbsp;|&nbsp; **Columns:** {df_processed.shape[1]}")
