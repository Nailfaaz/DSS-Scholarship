# pages/Page4_Ranking.py
"""
Tab 4 – Final Scholarship Ranking with BORDA Method

Flow:
1. Load results from SAW, WP, and TOPSIS scoring methods.
2. Compute ranks for each method (higher score → higher rank).
3. Calculate BORDA score by summing inverted ranks.
4. Display and save the final BORDA ranking table.
"""

import os
from pathlib import Path
import pandas as pd
import streamlit as st

# ---------- Constants ----------
BASE_DIR = Path(__file__).parent.parent
RESULT_DIR = BASE_DIR / "data" / "result"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

PATH_SAW = RESULT_DIR / "saw_result.csv"
PATH_WP = RESULT_DIR / "wp_result.csv"
PATH_TOPSIS = RESULT_DIR / "topsis_result.csv"
PATH_BORDA = RESULT_DIR / "borda_result.csv"

# ---------- Main Tab Function ----------

def ranking_tab() -> None:
    st.subheader("🏆 Final Scholarship Ranking - BORDA Method")

    # Check if all required scoring result files exist
    if not (PATH_SAW.exists() and PATH_WP.exists() and PATH_TOPSIS.exists()):
        st.error("SAW, WP, and TOPSIS results are incomplete. Please run scoring first.")
        return

    # Load score results
    df_saw = pd.read_csv(PATH_SAW)[["ID", "SAW_Score"]]
    df_wp = pd.read_csv(PATH_WP)[["ID", "WP_Score"]]
    df_topsis = pd.read_csv(PATH_TOPSIS)[["ID", "TOPSIS_Score"]]

    # Compute ranks (higher score → better rank, rank 1 is best)
    df_saw["Rank_SAW"] = df_saw["SAW_Score"].rank(ascending=False, method="min")
    df_wp["Rank_WP"] = df_wp["WP_Score"].rank(ascending=False, method="min")
    df_topsis["Rank_TOPSIS"] = df_topsis["TOPSIS_Score"].rank(ascending=False, method="min")


    # Merge ranks into single DataFrame
    df_rank = (
        df_saw[["ID", "Rank_SAW"]]
        .merge(df_wp[["ID", "Rank_WP"]], on="ID")
        .merge(df_topsis[["ID", "Rank_TOPSIS"]], on="ID")
    )

    # Calculate BORDA score (higher BORDA score is better)
    total_participants = len(df_rank)
    df_rank["Borda_Score"] = (
        (total_participants - df_rank["Rank_SAW"]) +
        (total_participants - df_rank["Rank_WP"]) +
        (total_participants - df_rank["Rank_TOPSIS"])
    )

    # Sort descending by BORDA score
    df_rank_sorted = df_rank.sort_values(by="Borda_Score", ascending=False).reset_index(drop=True)

    # Display ranking table
    st.markdown("### 📊 Final Ranking Table (BORDA)")
    st.dataframe(df_rank_sorted, use_container_width=True)

    # Save BORDA results to CSV
    df_rank_sorted.to_csv(PATH_BORDA, index=False)

    # Download button for BORDA result
    csv_borda = df_rank_sorted.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download BORDA Result",
        data=csv_borda,
        file_name="borda_result.csv",
        mime="text/csv",
    )
