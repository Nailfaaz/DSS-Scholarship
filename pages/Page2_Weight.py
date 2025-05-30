import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from typing import Dict, List, Tuple

# --- Konstanta dan Konfigurasi Dasar ---
DEFAULT_WEIGHT_FILE_PATH = "./data/weight/weight_default.csv" # Path default untuk file bobot
CUSTOM_WEIGHT_SAVE_PATH = "./data/weight/weight_custom.csv" # Path untuk menyimpan bobot kustom

CRITERION_DESCRIPTIONS = {
    'C1_GPA': 'Grade Point Average - Academic performance indicator',
    'C2_Certificates': 'Academic certificates and achievements',
    'C3_ParentIncomeIDR': 'Parent income in Indonesian Rupiah (financial need)',
    'C4_Dependents': 'Number of family dependents',
    'C5_OrgScore': 'Organizational involvement score',
    'C6_VolunteerEvents': 'Volunteer activities and community service',
    'C7_LetterScore': 'Recommendation letter quality score',
    'C8_InterviewScore': 'Interview performance score',
    'C9_DocComplete': 'Document completeness score',
    'C10_OnTime': 'Application submission timeliness'
}
CRITERIA_LIST = list(CRITERION_DESCRIPTIONS.keys())
RATING_OPTIONS = [1, 2, 3, 4, 5] # Opsi untuk rating bobot kustom

# --- Functions ---

def load_default_weights(file_path: str = DEFAULT_WEIGHT_FILE_PATH) -> Dict[str, float]:
    """Memuat bobot default dari file CSV.
    Kriteria diasumsikan sebagai header dan bobot berada di baris data pertama.
    """
    fallback_weights = {
        'C1_GPA': 0.1, 'C2_Certificates': 0.1, 'C3_ParentIncomeIDR': 0.1,
        'C4_Dependents': 0.1, 'C5_OrgScore': 0.1, 'C6_VolunteerEvents': 0.1,
        'C7_LetterScore': 0.1, 'C8_InterviewScore': 0.1, 'C9_DocComplete': 0.1,
        'C10_OnTime': 0.1
    }
    try:
        if os.path.exists(file_path):
            weights_df = pd.read_csv(file_path)
            if not weights_df.empty:
                # Ambil baris pertama dan konversi ke dictionary
                weights_dict = weights_df.iloc[0].to_dict()
                
                # Pastikan semua kriteria yang diharapkan ada dan nilainya float
                processed_weights = {}
                for criterion_code in CRITERIA_LIST: # Iterasi berdasarkan CRITERIA_LIST untuk konsistensi
                    if criterion_code in weights_dict:
                        try:
                            processed_weights[criterion_code] = float(weights_dict[criterion_code])
                        except ValueError:
                            st.error(f"Nilai bobot untuk '{criterion_code}' di file CSV ('{weights_dict[criterion_code]}') tidak valid. Menggunakan fallback.")
                            return fallback_weights
                    else:
                        st.warning(f"Kriteria '{criterion_code}' tidak ditemukan di file CSV. Menggunakan fallback.")
                        return fallback_weights # Jika ada kriteria penting yang hilang
                return processed_weights
            else:
                st.warning(f"File CSV '{file_path}' kosong. Menggunakan fallback weights.")
        else:
            st.info(f"File CSV '{file_path}' tidak ditemukan. Menggunakan fallback weights.")
        return fallback_weights
    except pd.errors.EmptyDataError: # Spesifik untuk file CSV kosong yang tidak bisa diparsing
        st.warning(f"File CSV '{file_path}' kosong atau format tidak benar. Menggunakan fallback weights.")
        return fallback_weights
    except Exception as e:
        st.error(f"Error memuat bobot default dari file '{file_path}': {str(e)}. Menggunakan fallback weights.")
        return fallback_weights

def validate_weights(weights: Dict[str, float]) -> bool:
    """Validasi apakah total bobot adalah 1.0 (dengan toleransi)."""
    if not weights:
        return False
    total = sum(weights.values())
    return abs(total - 1.0) < 0.001

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalisasi bobot sehingga totalnya menjadi 1.0."""
    if not weights:
        return {}
    total = sum(weights.values())
    if total > 0:
        return {k: v / total for k, v in weights.items()}
    return weights # Kembalikan bobot asli jika totalnya 0 untuk menghindari error

# --- Fungsi Helper UI ---

def format_criterion_label(criterion_code: str) -> str:
    """Format label kriteria agar lebih mudah dibaca (misal, 'GPA' dari 'C1_GPA')."""
    return re.sub(r'C[0-9]+_?', '', criterion_code).replace('_', ' ')

def display_weights_table_and_chart(
    weights_to_display: Dict[str, float], 
    is_normalized: bool, 
    title_prefix: str = "Current"
):
    """Menampilkan tabel, chart, dan metrik untuk bobot yang diberikan."""
    st.markdown(f"### 📊 {title_prefix} Weights")
    
    col_table, col_visualization = st.columns([2, 1])

    with col_table:
        df_data = []
        
        for crit, w in weights_to_display.items():
            df_data.append({
                'Criterion': crit,
                'Weight': f"{w:.3f}" if isinstance(w, float) and w < 1 else str(w), # Tampilkan rating mentah sebagai int
                'Description': CRITERION_DESCRIPTIONS.get(crit, 'N/A')
            })
        weights_df = pd.DataFrame(df_data)
        st.dataframe(weights_df, use_container_width=True, hide_index=True)

        if is_normalized: # Validasi hanya relevan jika kita mengharapkan normalisasi
            if validate_weights(weights_to_display):
                st.success("✅ Weights are properly normalized (sum ≈ 1.0)")
            else: # Seharusnya tidak terjadi jika is_normalized=True dan berasal dari proses normalisasi
                st.warning(f"⚠️ Weights sum to {sum(weights_to_display.values()):.3f}, but expected to be normalized.")
        # Tidak menampilkan validasi sum untuk bobot default yang mungkin tidak dinormalisasi dari file

    with col_visualization:
        st.markdown("**📈 Weight Distribution**")
        chart_data = {format_criterion_label(k): v for k, v in weights_to_display.items()}
        if chart_data:
            chart_df = pd.DataFrame(list(chart_data.items()), columns=['Criterion', 'Weight'])
            st.bar_chart(chart_df.set_index('Criterion'), height=300)
            
            weight_values = list(weights_to_display.values())
            if weight_values:
                st.metric("Highest Weight/Rating", f"{max(weight_values):.3f}" if isinstance(max(weight_values), float) and max(weight_values) < 1 else str(max(weight_values)))
                st.metric("Lowest Weight/Rating", f"{min(weight_values):.3f}" if isinstance(min(weight_values), float) and min(weight_values) < 1 else str(min(weight_values)))
                st.metric("Average Weight/Rating", f"{np.mean(weight_values):.3f}" if isinstance(np.mean(weight_values), float) and np.mean(weight_values) < 1 else f"{np.mean(weight_values):.1f}")
        else:
            st.caption("No valid weights to display in chart.")

def display_default_weights_config():
    """Menampilkan UI untuk konfigurasi bobot default."""
    st.info("🔍 **Default Weights Mode**: Load predefined weights from a CSV configuration file or use fallback defaults.")

    st.markdown("### 📂 File Configuration")
    col_file1, col_file2 = st.columns([3, 1])

    default_file_path_key = "default_weight_file_path_ui" # Key unik untuk text_input
    if default_file_path_key not in st.session_state:
        st.session_state[default_file_path_key] = DEFAULT_WEIGHT_FILE_PATH

    with col_file1:
        st.session_state[default_file_path_key] = st.text_input(
            "Weight Data File Path:",
            value=st.session_state[default_file_path_key],
            help=f"Path to CSV. Headers are criteria, first row is weights. Default: {DEFAULT_WEIGHT_FILE_PATH}"
        )
    with col_file2:
        st.write("") # Spacer
        st.write("") # Spacer
        if st.button("🔄 Load Default Weights", type="primary", use_container_width=True, key="load_default_btn"):
            with st.spinner("Loading default weights..."):
                loaded_w = load_default_weights(st.session_state[default_file_path_key])
                st.session_state.weights = loaded_w # Selalu update, bahkan jika fallback
                st.session_state.default_weights_loaded = True
                if loaded_w and loaded_w != load_default_weights(""):
                    if os.path.exists(st.session_state[default_file_path_key]) and os.path.getsize(st.session_state[default_file_path_key]) > 0:
                        st.success("✅ Default weights loaded successfully from file!")
                # Pesan info/warning sudah ditangani di dalam load_default_weights

    # Tampilkan bobot dan aksi hanya jika sudah klik tombol load
    if st.session_state.get("default_weights_loaded", False):
        if st.session_state.get('weights'):
            is_normalized_from_file = validate_weights(st.session_state.weights)
            display_weights_table_and_chart(st.session_state.weights, is_normalized_from_file, title_prefix="Default")
            if not is_normalized_from_file:
                st.warning(f"⚠️ Default weights from file sum to {sum(st.session_state.weights.values()):.3f}. They may need review if intended for direct DSS use without normalization step elsewhere.")
            display_action_buttons()
        else:
            st.warning("No default weights currently loaded. Check file path or fallback definitions.")

def display_custom_weights_config():
    """Menampilkan UI untuk konfigurasi bobot kustom."""
    st.info("🎯 **Custom Weights Mode**: Manually adjust the importance of each criterion using selection boxes (1 = Least Important, 5 = Most Important). Weights should be normalized to sum to 1.0 for proper analysis.")

    # Sinkronisasi raw_custom_ratings jika daftar kriteria berubah
    if set(st.session_state.raw_custom_ratings.keys()) != set(CRITERIA_LIST):
        current_raw_ratings = st.session_state.raw_custom_ratings.copy()
        st.session_state.raw_custom_ratings = {c: current_raw_ratings.get(c, 3) for c in CRITERIA_LIST}

    st.markdown("### ⚖️ Adjust Criterion Importance Ratings")
    st.markdown("*Use the selection boxes below to set the importance rating for each criterion (1 = Least Important, 5 = Most Important)*")

    ratings_before_ui = st.session_state.raw_custom_ratings.copy()
    temp_raw_ratings_from_ui = {}
    mid_point = len(CRITERIA_LIST) // 2

    input_col1, input_col2 = st.columns(2)
    with input_col1:
        st.markdown(f"**Criteria 1-{mid_point}**")
        for criterion in CRITERIA_LIST[:mid_point]:
            temp_raw_ratings_from_ui[criterion] = st.selectbox(
                label=f"{format_criterion_label(criterion)}:",
                options=RATING_OPTIONS,
                index=RATING_OPTIONS.index(st.session_state.raw_custom_ratings.get(criterion, 3)),
                help=CRITERION_DESCRIPTIONS[criterion],
                key=f"select_{criterion}"
            )
            st.caption(CRITERION_DESCRIPTIONS[criterion])
    with input_col2:
        st.markdown(f"**Criteria {mid_point + 1}-{len(CRITERIA_LIST)}**")
        for criterion in CRITERIA_LIST[mid_point:]:
            temp_raw_ratings_from_ui[criterion] = st.selectbox(
                label=f"{format_criterion_label(criterion)}:",
                options=RATING_OPTIONS,
                index=RATING_OPTIONS.index(st.session_state.raw_custom_ratings.get(criterion, 3)),
                help=CRITERION_DESCRIPTIONS[criterion],
                key=f"select_{criterion}"
            )
            st.caption(CRITERION_DESCRIPTIONS[criterion])
    
    st.session_state.raw_custom_ratings = temp_raw_ratings_from_ui.copy()

    if ratings_before_ui != st.session_state.raw_custom_ratings:
        st.session_state.custom_weights_are_normalized = False

    if not st.session_state.custom_weights_are_normalized:
        st.session_state.weights = st.session_state.raw_custom_ratings.copy()
    
    # Tampilkan ringkasan dan validasi untuk bobot kustom
    display_weight_summary_and_validation(st.session_state.weights, st.session_state.custom_weights_are_normalized)

    # Bagian Normalisasi
    if not st.session_state.custom_weights_are_normalized:
        st.markdown("### 🔄 Weight Normalization")
        current_sum = sum(st.session_state.weights.values()) if st.session_state.weights else 0
        st.warning(f"⚠️ Current sum of ratings is {int(current_sum)}. For proper analysis, weights should sum to 1.0.")
        
        norm_col1, norm_col2 = st.columns([1, 3])
        with norm_col1:
            if st.button("🔄 Normalize Weights", type="primary", use_container_width=True, key="normalize_custom_btn"):
                normalized_w = normalize_weights(st.session_state.raw_custom_ratings)
                st.session_state.weights = normalized_w
                st.session_state.custom_weights_are_normalized = True
                st.success("✅ Weights have been normalized!")
                st.rerun()
        with norm_col2:
            st.info("Normalization will proportionally adjust all ratings so they sum to exactly 1.0.")

def display_weight_summary_and_validation(current_weights: Dict[str, float], is_normalized_flag: bool):
    """Menampilkan ringkasan bobot (tabel, chart, statistik) untuk mode kustom."""
    st.markdown("---")
    st.markdown("### 📊 Weight Summary & Validation")
    
    total_weight_val = sum(current_weights.values()) if current_weights else 0

    summary_col_table, summary_col_visualization, summary_col_stats = st.columns([2, 1, 1])
    
    with summary_col_table:
        st.markdown("**Current Values**")
        summary_df_data = []
        for criterion, weight_val in current_weights.items():
            is_raw_int_rating = isinstance(weight_val, int) and weight_val in RATING_OPTIONS and not is_normalized_flag
            display_val = str(weight_val) if is_raw_int_rating else f"{weight_val:.3f}"

            summary_df_data.append({
                'Criterion': format_criterion_label(criterion),
                'Value/Weight': display_val,
                'Description': CRITERION_DESCRIPTIONS.get(criterion, 'N/A'),
            })
        summary_df = pd.DataFrame(summary_df_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with summary_col_visualization:
        st.markdown("**📈 Visualization**")
        chart_data = {format_criterion_label(k): v for k, v in current_weights.items()}
        if chart_data:
            chart_df = pd.DataFrame(list(chart_data.items()), columns=['Criterion', 'Weight'])
            st.bar_chart(chart_df.set_index('Criterion'), height=250)
        else:
            st.caption("No data for chart.")

    with summary_col_stats:
        st.markdown("**📊 Statistics**")
        if is_normalized_flag:
            st.metric("Total Normalized Weight", f"{total_weight_val:.3f}")
            st.metric("Total Percentage", f"{total_weight_val*100:.1f}%")
            st.success("✅ Normalized")
        else:
            st.metric("Sum of Ratings", f"{int(total_weight_val)}")
            st.warning("⚠️ Not Normalized")
        
        weights_values_list = list(current_weights.values()) if current_weights else []
        if weights_values_list:
            max_v = max(weights_values_list)
            min_v = min(weights_values_list)
            mean_v = np.mean(weights_values_list)
            st.metric("Highest", str(int(max_v)) if isinstance(max_v, int) and not is_normalized_flag else f"{max_v:.3f}")
            st.metric("Lowest", str(int(min_v)) if isinstance(min_v, int) and not is_normalized_flag else f"{min_v:.3f}")
            st.metric("Average", f"{mean_v:.1f}" if not is_normalized_flag else f"{mean_v:.3f}")

def display_action_buttons():
    """Menampilkan tombol aksi utama (Save, Continue)."""
    st.markdown("---")
    st.info("Jika sudah yakin, simpan bobot yang telah diatur untuk melanjutkan ke langkah berikutnya.")
    
    # Membuat direktori jika belum ada (untuk penyimpanan CSV)
    if not os.path.exists("data/weight"):
        try:
            os.makedirs("data/weight")
        except OSError as e:
            st.error(f"Gagal membuat direktori 'data/weight': {e}. Penyimpanan CSV mungkin gagal.")

    if st.button("💾 Save Weights", type="primary", use_container_width=True, key="save_weights_btn"):
        if st.session_state.weights:
            if st.session_state.weight_method == 'custom' and not st.session_state.custom_weights_are_normalized:
                st.warning("⚠️ Saving unnormalized custom ratings. Consider normalizing first for DSS calculations.")
            
            try:
                # Simpan sebagai DataFrame dengan satu baris, di mana header adalah kriteria
                df_to_save = pd.DataFrame([st.session_state.weights])
                save_path = CUSTOM_WEIGHT_SAVE_PATH if st.session_state.weight_method == 'custom' else DEFAULT_WEIGHT_FILE_PATH # Atau path lain untuk default yang diedit
                
                # Jika menyimpan bobot default (misalnya setelah diedit atau hanya ingin menyimpan ulang),
                # mungkin ingin path yang berbeda atau konfirmasi. Untuk saat ini, custom path.
                if st.session_state.weight_method == 'default':
                    save_path = st.session_state.get("default_weight_file_path_ui", DEFAULT_WEIGHT_FILE_PATH)
                    st.info(f"Menyimpan bobot default ke: {save_path}")


                df_to_save.to_csv(save_path, index=False)
                st.success(f"✅ Weights saved successfully to '{save_path}'! You can continue.")
            except Exception as e:
                st.error(f"❌ Failed to save weights: {str(e)}")
        else:
            st.error("❌ No weights to save.")

# --- Fungsi Utama Tab ---

def weight_tab():
    """Fungsi utama untuk menampilkan tab konfigurasi bobot."""
    
    # Inisialisasi session state jika belum ada
    if 'weights' not in st.session_state:
        # Load bobot default saat pertama kali jika metode default, atau kosongkan untuk custom
        if st.session_state.get('weight_method', 'default') == 'default':
            st.session_state.weights = load_default_weights()
        else:
            st.session_state.weights = {} # Akan diisi oleh raw_custom_ratings
            
    if 'weight_method' not in st.session_state:
        st.session_state.weight_method = 'default'
    if 'raw_custom_ratings' not in st.session_state:
        st.session_state.raw_custom_ratings = {criterion: 3 for criterion in CRITERIA_LIST}
    if 'custom_weights_are_normalized' not in st.session_state:
        st.session_state.custom_weights_are_normalized = False
    if "default_weight_file_path_ui" not in st.session_state: # Untuk text input UI
        st.session_state.default_weight_file_path_ui = DEFAULT_WEIGHT_FILE_PATH


    st.subheader("🎯 Select Weighting Method")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button("📁 Default Weights", key="btn_default_method",
                      type="primary" if st.session_state.weight_method == 'default' else "secondary",
                      use_container_width=True):
            if st.session_state.weight_method != 'default': # Hanya jika ada perubahan
                st.session_state.weight_method = 'default'
                st.session_state.custom_weights_are_normalized = False
                st.session_state.weights = load_default_weights(st.session_state.default_weight_file_path_ui)
                st.rerun()
    with col_m2:
        if st.button("🎛️ Custom Weights", key="btn_custom_method",
                      type="primary" if st.session_state.weight_method == 'custom' else "secondary",
                      use_container_width=True):
            if st.session_state.weight_method != 'custom': # Hanya jika ada perubahan
                st.session_state.weight_method = 'custom'
                # Saat beralih ke custom, jika belum dinormalisasi, bobot harus mencerminkan rating mentah
                if not st.session_state.custom_weights_are_normalized:
                    st.session_state.weights = st.session_state.raw_custom_ratings.copy()
                # Jika sudah dinormalisasi sebelumnya, biarkan st.session_state.weights (yang berisi nilai normalisasi)
                st.rerun()
    st.markdown("---")

    # Tampilkan konten berdasarkan metode yang dipilih
    if st.session_state.weight_method == 'default':
        display_default_weights_config()
    else: # 'custom'
        display_custom_weights_config()

    # Tombol aksi selalu ditampilkan
    # display_action_buttons()

