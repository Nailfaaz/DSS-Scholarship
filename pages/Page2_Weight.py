import streamlit as st
import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/preprocessed/scholarship_sample.csv")

def criteria_tab():
    """
    Page 2 – Data preview.

    • First tries the DataFrame already stored in st.session_state["data"]
      (set on Page 1 after upload / selection).
    • If nothing is there, falls back to data/preprocessed/scholarship_sample.csv.
    """
    st.header("2. Review / Preview Data")

    # ── Load dataset ────────────────────────────────────────────────
    if "data" not in st.session_state or st.session_state["data"] is None:
        if DATA_PATH.exists():
            st.session_state["data"] = pd.read_csv(DATA_PATH)
        else:
            st.info("📂 No dataset found. Please upload on Page 1 first "
                    f"or place a CSV at {DATA_PATH}.")
            return

    df = st.session_state["data"]

    # ── Display ────────────────────────────────────────────────────
    st.subheader("Dataset snapshot")
    st.dataframe(df, use_container_width=True)          # interactive view

    st.markdown(f"**Rows:** {df.shape[0]} &nbsp;|&nbsp; **Columns:** {df.shape[1]}")
