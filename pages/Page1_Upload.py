import os
import pandas as pd
import streamlit as st

# Folder for validated user datasets
DATA_DIR = os.path.join(os.getcwd(), "data", "input")
os.makedirs(DATA_DIR, exist_ok=True)

# Expected schema
EXPECTED_COLUMNS = [
    "ID", "C1_GPA", "C2_Certificates", "C3_ParentIncomeIDR",
    "C4_Dependents", "C5_OrgScore", "C6_VolunteerEvents",
    "C7_LetterScore", "C8_InterviewScore", "C9_DocComplete", "C10_OnTime"
]

def upload_tab():
    st.header("1. Upload / Choose Data")
    st.caption("Upload a CSV **or** pick one already in `data/input/`."
               "  • Uploaded files are **saved only if they pass validation.**")

    # ---------- Existing datasets ----------
    file_list = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".csv")]
    file_list.insert(0, "-- Select --")
    choice = st.selectbox("Choose an existing dataset:", file_list)

    # ---------- File uploader --------------
    uploaded_file = st.file_uploader("Or upload a new CSV", type="csv")

    # Decide our data source
    df, source_name, is_uploaded = None, None, False

    if uploaded_file is not None:
        # User just uploaded something
        source_name, is_uploaded = uploaded_file.name, True
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"❌ Unable to read *{source_name}*: {e}")
            return

    elif choice != "-- Select --":
        # User picked an existing file
        source_name = choice
        try:
            df = pd.read_csv(os.path.join(DATA_DIR, choice))
        except Exception as e:
            st.error(f"❌ Unable to read *{choice}*: {e}")
            return
    else:
        st.info("📂 Please upload a CSV or choose one from the list.")
        return

    # ---------- Validate -------------------
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    nan_cols     = df.columns[df.isnull().any()].tolist()

    if missing_cols:
        st.error(f"❌ Missing columns: {', '.join(missing_cols)}")
        return
    if nan_cols:
        st.error(f"❌ Dataset contains missing values in: {', '.join(nan_cols)}")
        return

    # ---------- Save only if uploaded & valid
    if is_uploaded:
        dest_path = os.path.join(DATA_DIR, source_name)
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ *{source_name}* validated **and saved** to `data/input/`.")
    else:
        st.success(f"✅ *{source_name}* loaded successfully.")

    # ---------- Store + preview ------------
    st.session_state.df = df
    st.subheader("Data preview")
    st.dataframe(df, use_container_width=True)
    st.markdown(f"**Rows:** {df.shape[0]} &nbsp;|&nbsp; **Columns:** {df.shape[1]}")
