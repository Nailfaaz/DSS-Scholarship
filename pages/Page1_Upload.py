import os
import pandas as pd
import streamlit as st

# Directory where input CSVs are stored
DATA_DIR = os.path.join(os.getcwd(), "data", "input")

# Expected columns
EXPECTED_COLUMNS = [
    "ID",
    "C1_GPA",
    "C2_Certificates",
    "C3_ParentIncomeIDR",
    "C4_Dependents",
    "C5_OrgScore",
    "C6_VolunteerEvents",
    "C7_LetterScore",
    "C8_InterviewScore",
    "C9_DocComplete",
    "C10_OnTime"
]


def upload_tab():
    st.header("1. Upload / Choose Data")
    st.write("Select an existing dataset from `data/input` or upload a new one.")

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # List existing CSV files
    files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.csv')]
    files.insert(0, "-- Select --")

    choice = st.selectbox("Choose a dataset:", files)
    uploaded_file = st.file_uploader("Or upload your own CSV file", type=["csv"])

    df = None
    # Process upload
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Unable to read uploaded file: {e}")
            return

        # Save to data/input
        dest_path = os.path.join(DATA_DIR, uploaded_file.name)
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Uploaded and saved `{uploaded_file.name}` to `data/input`.")

    # Process selection
    elif choice and choice != "-- Select --":
        path = os.path.join(DATA_DIR, choice)
        try:
            df = pd.read_csv(path)
        except Exception as e:
            st.error(f"Unable to read `{choice}`: {e}")
            return

        st.success(f"Loaded `{choice}` successfully.")

    else:
        st.info("Please select a dataset or upload one.")
        return

    # Validate dataframe
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        st.error(f"Dataset is missing required columns: {', '.join(missing_cols)}")
        return

    # Check for NaNs
    nan_cols = df.columns[df.isnull().any()].tolist()
    if nan_cols:
        st.error(f"Dataset contains missing values in columns: {', '.join(nan_cols)}")
        return

    # Store in session and display
    st.session_state.df = df
    st.write("### Loaded Data Preview")
    st.dataframe(df)
