import os
import pandas as pd
import streamlit as st

# Constants
data_dir = os.path.join(os.getcwd(), "spk", "data") if "spk" in os.getcwd() else "data"

# --- Tab functions ---
def upload_tab():
    st.header("1. Upload / Choose Data")
    st.write("Select an existing dataset or upload a new one.")

    # List existing CSVs
    try:
        files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    except FileNotFoundError:
        files = []
    files.insert(0, "-- Select --")
    choice = st.selectbox("Choose a dataset:", files)

    uploaded = st.file_uploader("Or upload your own CSV", type=["csv"])

    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.session_state.df = df
        st.success(f"Loaded uploaded dataset ({len(df)} rows)")
    elif choice != "-- Select --":
        path = os.path.join(data_dir, choice)
        df = pd.read_csv(path)
        st.session_state.df = df
        st.success(f"Loaded '{choice}' ({len(df)} rows)")
    else:
        st.info("Please select a dataset from the dropdown or upload one.")


def preprocess_tab():
    st.header("2. Preprocessing")
    st.write("Inspect and clean the loaded dataset.")
    if "df" in st.session_state:
        df = st.session_state.df
        st.dataframe(df)
        # TODO: add options to drop/mask missing values
    else:
        st.warning("No dataset loaded. Go to the first tab to load data.")


def criteria_tab():
    st.header("3. Define Criteria")
    st.write("Set weights and directions for each criterion.")
    # TODO: sliders for weights (sum to 1) and toggles for benefit/cost


def run_tab():
    st.header("4. Run & Results")
    st.write("Execute the SAW algorithm and view rankings.")
    if "df" not in st.session_state:
        st.warning("No dataset loaded.")
        return
    # TODO: retrieve weights and benefit list
    if st.button("Run SAW"):
        # placeholder: stub
        st.info("SAW run not yet implemented.")


def export_tab():
    st.header("5. Export Results")
    st.write("Download the ranked results once available.")
    if "df" in st.session_state:
        # TODO: enable CSV/Excel download of results
        st.info("Export functionality coming soon.")
    else:
        st.warning("No results to export.")


def main():
    st.set_page_config(page_title="Undergraduate Scholarship DSS", layout="wide")
    st.title("Undergraduate Scholarship DSS")

    tabs = st.tabs([
        "Upload / Choose",
        "Preprocessing",
        "Define Criteria",
        "Run & Results",
        "Export"
    ])

    for tab, func in zip(tabs, [upload_tab, preprocess_tab, criteria_tab, run_tab, export_tab]):
        with tab:
            func()

if __name__ == "__main__":
    main()