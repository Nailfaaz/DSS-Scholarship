# pages/Page1_Upload.py
"""
Tab 1 – Upload / Choose Data

Flow:
1.  Offer a downloadable CSV template (data/template/template.csv).
2.  Let the user:
      • pick an existing CSV in data/input/, or
      • upload their own CSV.
3.  Validate schema + NaNs.
4.  Pre-process C3_ParentIncomeIDR → 1-to-5 band score.
5.  Save:
      • original file (if uploaded) → data/input/
      • pre-processed file         → data/preprocessed/{name}_preprocessed.csv
6.  Store DataFrame in st.session_state.df and preview it.
"""

import os
from pathlib import Path
import pandas as pd
import streamlit as st

# ---------- directory setup (paths are relative to this script) ----------
HERE         = Path(__file__).parent            # …/pages/
BASE_DIR     = HERE.parent                      # project root (contains app.py)
INPUT_DIR    = BASE_DIR / "data" / "input"
PREPROC_DIR  = BASE_DIR / "data" / "preprocessed"
TEMPLATE_DIR = BASE_DIR / "data" / "template"
TEMPLATE_PATH = TEMPLATE_DIR / "template.csv"

# Ensure folders exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
PREPROC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# ---------- expected columns ----------
EXPECTED_COLUMNS = [
    "ID", "C1_GPA", "C2_Certificates", "C3_ParentIncomeIDR",
    "C4_Dependents", "C5_OrgScore", "C6_VolunteerEvents",
    "C7_LetterScore", "C8_InterviewScore", "C9_DocComplete", "C10_OnTime"
]

# ---------- helper: income band → score ----------
def map_income_to_score(idr: float) -> int:
    """
    0 – <4 M IDR  → 4
    4 – <6 M IDR  → 5
    6 – <10 M IDR → 3
    10 – <20 M IDR→ 2
    ≥ 20 M IDR    → 1
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


# ======================================================================
def upload_tab() -> None:
    st.header("1 . Upload / Choose Data")

    # ---------- template download ----------
    with st.expander("📄 Download CSV template", expanded=True):
        if TEMPLATE_PATH.exists():
            with open(TEMPLATE_PATH, "rb") as f:
                st.download_button(
                    "⬇️  Save template",
                    data=f.read(),
                    file_name="scholarship_template.csv",
                    mime="text/csv",
                )
        else:
            st.error(f"Template not found at {TEMPLATE_PATH}")

    st.markdown("---")

    # ---------- existing datasets ----------
    existing = ["-- Select --"] + [p.name for p in INPUT_DIR.glob("*.csv")]
    choice = st.selectbox("Choose a dataset in *data/input/*:", existing)

    # ---------- uploader ----------
    uploaded = st.file_uploader("Or upload a new CSV", type="csv")

    # ---------- decide data source ----------
    df, src_name, is_uploaded = None, None, False

    if uploaded is not None:
        src_name, is_uploaded = uploaded.name, True
        try:
            df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"❌ Unable to read **{src_name}**: {e}")
            return

    elif choice != "-- Select --":
        src_name = choice
        try:
            df = pd.read_csv(INPUT_DIR / choice)
        except Exception as e:
            st.error(f"❌ Unable to read **{choice}**: {e}")
            return
    else:
        st.info("📂 Choose a dataset or upload one, then continue.")
        return

    # ---------- validation ----------
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"❌ Missing columns: {', '.join(missing)}")
        return

    nan_cols = df.columns[df.isnull().any()].tolist()
    if nan_cols:
        st.error(f"❌ Dataset contains missing values in: {', '.join(nan_cols)}")
        return

    # ---------- preprocessing ----------
    try:
        # strip any thousand separators / non-digits, convert to float
        df["C3_ParentIncomeIDR"] = (
            df["C3_ParentIncomeIDR"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True)
            .astype(float)
            .apply(map_income_to_score)
        )
    except Exception as e:
        st.error(f"❌ Failed to preprocess **C3_ParentIncomeIDR**: {e}")
        return

    # ---------- save pre-processed ----------
    preproc_name = f"{Path(src_name).stem}_preprocessed.csv"
    df.to_csv(PREPROC_DIR / preproc_name, index=False)

    # save original upload (only after validation)
    if is_uploaded:
        uploaded.seek(0)
        with open(INPUT_DIR / src_name, "wb") as f:
            f.write(uploaded.getbuffer())

    st.success(
        f"✅ Pre-processed file saved as **{preproc_name}** in *data/preprocessed/*. "
        "Data is ready for the next step."
    )

    # ---------- hand off & preview ----------
    st.session_state.df = df
    st.subheader("Preview of Pre-processed Data")
    st.dataframe(df, use_container_width=True)
    st.markdown(f"**Rows:** {df.shape[0]} &nbsp;|&nbsp; **Columns:** {df.shape[1]}")
