import streamlit as st
import pandas as pd
import numpy as np
import os
import io

def scoring_tab():
    st.subheader("🎯 Skoring Beasiswa")

    # Load preprocessed data
    # Dapatkan path absolut dari direktori file ini (pages/)
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Naik satu level ke root project (DSS-Scholarship/)
    ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))

    # Path ke file preprocessed dan hasil
    PREPROCESSED_PATH = os.path.join(ROOT_DIR, "data", "preprocessed", "scholarship_sample_preprocessed.csv")
    RESULT_DIR = os.path.join(ROOT_DIR, "data", "result")
    os.makedirs(RESULT_DIR, exist_ok=True)

    df = pd.read_csv(PREPROCESSED_PATH)

    # Pilih path bobot berdasarkan metode
    if st.session_state.get("weight_method") == "Custom Weights":
        WEIGHT_PATH = os.path.join(ROOT_DIR, "data", "weight", "weight_custom.csv")
    else:
        WEIGHT_PATH = os.path.join(ROOT_DIR, "data", "weight", "weight_default.csv")

    # Load weights
    if "weighted_df" in st.session_state:
        weights_df = st.session_state.weighted_df.copy()
    else:
        try:
            raw_weights = pd.read_csv(WEIGHT_PATH)
            weights_df = pd.DataFrame({
                "Kriteria": raw_weights.columns,
                "Bobot": raw_weights.iloc[0].values
            })
        except FileNotFoundError:
            st.error("File bobot tidak ditemukan. Silakan atur bobot terlebih dahulu.")
            return
        
    weights = weights_df["Bobot"].values
    kriteria = weights_df["Kriteria"].values

    # Asumsikan semua kriteria adalah benefit
    types = ["Benefit"] * len(kriteria)

    # Pilihan metode skoring
    st.markdown("#### Pilih Metode Skoring")
    col1, col2, col3 = st.columns(3)
    with col1:
        use_saw = st.checkbox("SAW (Simple Additive Weighting)")
    with col2:
        use_wp = st.checkbox("WP (Weighted Product)")
    with col3:
        use_topsis = st.checkbox("TOPSIS")

    # Hitung skor jika ada metode yang dipilih
    if any([use_saw, use_wp, use_topsis]):
        st.markdown("### 📊 Hasil Skoring")

        # Ambil kolom fitur (C1 - C10)
        features = df[kriteria].copy()

        def save_result(method_name, result_df):
            output_path = f"data/result/{method_name.lower()}_result.csv"
            os.makedirs("data/result", exist_ok=True)
            result_df.to_csv(output_path, index=False)

        if use_saw:
            st.markdown("#### 🔹 SAW Result")
            norm = features / features.max()
            scores = norm.dot(weights)

            df_saw = df.copy()
            df_saw["Skor_SAW"] = scores
            df_saw = df_saw.sort_values(by="Skor_SAW", ascending=False)

            st.dataframe(df_saw[["ID", "Skor_SAW"]].reset_index(drop=True), use_container_width=True)
            save_result("SAW", df_saw)

            csv_saw = df_saw.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Hasil SAW",
                data=csv_saw,
                file_name='saw_result.csv',
                mime='text/csv'
            )

        if use_wp:
            st.markdown("#### 🔹 WP Result")
            wp_matrix = features.replace(0, 1e-6)
            log_matrix = np.log(wp_matrix) * weights
            log_sum = log_matrix.sum(axis=1)
            scores = np.exp(log_sum)

            df_wp = df.copy()
            df_wp["Skor_WP"] = scores
            df_wp = df_wp.sort_values(by="Skor_WP", ascending=False)

            st.dataframe(df_wp[["ID", "Skor_WP"]].reset_index(drop=True), use_container_width=True)
            save_result("WP", df_wp)

            csv_wp = df_wp.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Hasil WP",
                data=csv_wp,
                file_name='wp_result.csv',
                mime='text/csv'
            )

        if use_topsis:
            st.markdown("#### 🔹 TOPSIS Result")
            norm = features / np.sqrt((features**2).sum())
            weighted = norm * weights

            ideal_pos = weighted.max()
            ideal_neg = weighted.min()

            dist_pos = np.sqrt(((weighted - ideal_pos) ** 2).sum(axis=1))
            dist_neg = np.sqrt(((weighted - ideal_neg) ** 2).sum(axis=1))

            scores = dist_neg / (dist_pos + dist_neg)

            df_topsis = df.copy()
            df_topsis["Skor_TOPSIS"] = scores
            df_topsis = df_topsis.sort_values(by="Skor_TOPSIS", ascending=False)

            st.dataframe(df_topsis[["ID", "Skor_TOPSIS"]].reset_index(drop=True), use_container_width=True)
            save_result("TOPSIS", df_topsis)

            csv_topsis = df_topsis.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Hasil TOPSIS",
                data=csv_topsis,
                file_name='topsis_result.csv',
                mime='text/csv'
            )

    else:
        st.info("Silakan pilih setidaknya satu metode untuk menghitung skor.")
