import streamlit as st
import pandas as pd
import os

def ranking_tab():
    st.subheader("🏆 Ranking Akhir Beasiswa - Metode BORDA")

    # Dapatkan direktori saat ini dan direktori root
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
    RESULT_DIR = os.path.join(ROOT_DIR, "data", "result")
    os.makedirs(RESULT_DIR, exist_ok=True)

    # Path ke hasil masing-masing metode
    path_saw = os.path.join(RESULT_DIR, "saw_result.csv")
    path_wp = os.path.join(RESULT_DIR, "wp_result.csv")
    path_topsis = os.path.join(RESULT_DIR, "topsis_result.csv")

    # Pastikan semua file ada
    if not (os.path.exists(path_saw) and os.path.exists(path_wp) and os.path.exists(path_topsis)):
        st.error("Hasil dari SAW, WP, dan TOPSIS belum lengkap. Silakan lakukan skoring terlebih dahulu.")
        return

    # Load hasil dari ketiga metode
    df_saw = pd.read_csv(path_saw)[["ID", "Skor_SAW"]]
    df_wp = pd.read_csv(path_wp)[["ID", "Skor_WP"]]
    df_topsis = pd.read_csv(path_topsis)[["ID", "Skor_TOPSIS"]]

    # Hitung ranking (semakin tinggi skor, ranking makin tinggi)
    df_saw["Rank_SAW"] = df_saw["Skor_SAW"].rank(ascending=False, method="min")
    df_wp["Rank_WP"] = df_wp["Skor_WP"].rank(ascending=False, method="min")
    df_topsis["Rank_TOPSIS"] = df_topsis["Skor_TOPSIS"].rank(ascending=False, method="min")

    # Gabungkan ranking
    df_rank = df_saw[["ID", "Rank_SAW"]].merge(
        df_wp[["ID", "Rank_WP"]], on="ID"
    ).merge(
        df_topsis[["ID", "Rank_TOPSIS"]], on="ID"
    )

    # Hitung skor BORDA (semakin rendah rank, semakin tinggi skor)
    total_participants = len(df_rank)
    df_rank["Borda_Score"] = (
        (total_participants - df_rank["Rank_SAW"]) +
        (total_participants - df_rank["Rank_WP"]) +
        (total_participants - df_rank["Rank_TOPSIS"])
    )

    # Urutkan berdasarkan skor BORDA tertinggi
    df_rank_sorted = df_rank.sort_values(by="Borda_Score", ascending=False).reset_index(drop=True)

    st.markdown("### 📊 Tabel Ranking Akhir (BORDA)")
    st.dataframe(df_rank_sorted, use_container_width=True)

    # Simpan ke CSV
    borda_path = os.path.join(RESULT_DIR, "borda_result.csv")
    df_rank_sorted.to_csv(borda_path, index=False)

    # Tombol download
    csv_borda = df_rank_sorted.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Hasil BORDA",
        data=csv_borda,
        file_name="borda_result.csv",
        mime="text/csv"
    )
