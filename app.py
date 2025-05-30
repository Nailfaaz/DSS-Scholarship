# app.py  – tabs only, zero sidebar
import streamlit as st

# ---------------- page modules -----------------
from pages.Page1_Upload import upload_tab
from pages.Page2_Weight import weight_tab
# from pages.Page3_Scoring import scoring_tab

# ------------ App configuration ---------------
st.set_page_config(
    page_title="Undergraduate Scholarship DSS",
    layout="wide",
    initial_sidebar_state="collapsed",  # start collapsed
)

# ------ 🔒 Hide sidebar & hamburger -----------
HIDE_SIDEBAR = """
<style>
/* Completely remove the sidebar */
[data-testid="stSidebar"] {display: none !important;}
/* Hide the hamburger (collapsed sidebar) icon */
[data-testid="collapsedControl"] {display: none !important;}
</style>
"""
st.markdown(HIDE_SIDEBAR, unsafe_allow_html=True)

# ----------------- Title ----------------------
st.title("Undergraduate Scholarship DSS")

# ----------------- Tabs -----------------------
tabs = st.tabs([
    "1. Upload / Choose Data",
    "2. Weight Criteria",
    # "3. Scoring & Results",
])

with tabs[0]:
    upload_tab()

with tabs[1]:
    weight_tab()