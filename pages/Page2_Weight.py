import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from typing import Dict

def load_default_weights(file_path: str = "data/weight/weight_default.csv") -> Dict[str, float]:
    """Load default weights from CSV file where criteria are headers and weights are in the first data row."""
    fallback_weights = {
        'C1_GPA': 0.1,
        'C2_Certificates': 0.1,
        'C3_ParentIncomeIDR': 0.1,
        'C4_Dependents': 0.1,
        'C5_OrgScore': 0.1,
        'C6_VolunteerEvents': 0.1,
        'C7_LetterScore': 0.1,
        'C8_InterviewScore': 0.1,
        'C9_DocComplete': 0.1,
        'C10_OnTime': 0.1
    }
    
    try:
        if os.path.exists(file_path):
            weights_df = pd.read_csv(file_path)
            if not weights_df.empty:
                # Baris pertama dari DataFrame berisi bobot,
                # dan nama kolom DataFrame adalah nama kriteria.
                # Kita ambil baris pertama dan ubah menjadi dictionary.
                weights_dict = weights_df.iloc[0].to_dict()
                
                # Pastikan semua nilai bobot adalah float
                # (Meskipun pd.read_csv biasanya sudah mendeteksinya sebagai float jika hanya angka)
                for key in weights_dict:
                    try:
                        weights_dict[key] = float(weights_dict[key])
                    except ValueError:
                        st.error(f"Nilai bobot untuk '{key}' di file CSV tidak valid: {weights_dict[key]}. Harap periksa file.")
                        # Anda bisa memutuskan untuk mengembalikan dict kosong atau fallback di sini jika ada error konversi
                        return fallback_weights # Fallback jika ada error konversi nilai
                return weights_dict
            else:
                st.warning(f"File CSV '{file_path}' kosong. Menggunakan fallback weights.")
        else:
            st.info(f"File CSV '{file_path}' tidak ditemukan. Menggunakan fallback weights.")
        
        # Fallback default weights jika file tidak ada, kosong, atau ada error yang tidak ditangani di atas
        return fallback_weights
    except Exception as e:
        st.error(f"Error memuat bobot default dari file '{file_path}': {str(e)}. Menggunakan fallback weights.")
        # Fallback jika ada exception lain yang tidak terduga
        return fallback_weights

def validate_weights(weights: Dict[str, float]) -> bool:
    """Validate that weights sum to 1.0"""
    if not weights: # Handle empty weights case
        return False
    total = sum(weights.values())
    return abs(total - 1.0) < 0.001  # Allow small floating point errors

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize weights to sum to 1.0"""
    if not weights: # Handle empty weights case
        return {}
    total = sum(weights.values())
    if total > 0:
        return {k: v / total for k, v in weights.items()}
    return weights


def weight_tab():
    # Header
    st.header("Criterion Weighting Configuration")
    st.markdown("Configure the importance weights for each evaluation criterion used in the scholarship selection process.")
    st.markdown("---")

    criterion_descriptions = {
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
    criteria_list = list(criterion_descriptions.keys())

    # Initialize session state
    if 'weights' not in st.session_state:
        st.session_state.weights = {}
    if 'weight_method' not in st.session_state:
        st.session_state.weight_method = 'default'
    if 'raw_custom_ratings' not in st.session_state:
        st.session_state.raw_custom_ratings = {criterion: 3 for criterion in criteria_list}
    
    # Flag for normalization status of custom weights
    if 'custom_weights_are_normalized' not in st.session_state:
        st.session_state.custom_weights_are_normalized = False

    st.subheader("🎯 Select Weighting Method")
    col_method1, col_method2 = st.columns(2)

    with col_method1:
        if st.button("📁 Default Weights",
                      type="primary" if st.session_state.weight_method == 'default' else "secondary",
                      use_container_width=True):
            st.session_state.weight_method = 'default'
            st.session_state.custom_weights_are_normalized = False # Reset flag
            # Load default weights immediately upon switching
            st.session_state.weights = load_default_weights(st.session_state.get("default_weight_file_path", "data/weight/weight_default.csv"))
            if not st.session_state.weights: # If loading from specific path fails, try fallback
                 st.session_state.weights = load_default_weights("")
            st.rerun()

    with col_method2:
        if st.button("🎛️ Custom Weights",
                      type="primary" if st.session_state.weight_method == 'custom' else "secondary",
                      use_container_width=True):
            st.session_state.weight_method = 'custom'
            # Ensure raw_custom_ratings are initialized
            if not st.session_state.raw_custom_ratings or \
               set(st.session_state.raw_custom_ratings.keys()) != set(criteria_list):
                st.session_state.raw_custom_ratings = {criterion: 3 for criterion in criteria_list}
            
            # If not already normalized, or if switching to custom, weights should reflect raw ratings
            if not st.session_state.custom_weights_are_normalized:
                 st.session_state.weights = st.session_state.raw_custom_ratings.copy()
            # If they ARE normalized, st.session_state.weights already has them.
            st.rerun()
    st.markdown("---")

    if st.session_state.weight_method == 'default':
        st.subheader("📁 Default Weights Configuration")
        st.info("🔍 **Default Weights Mode**: Load predefined weights from a CSV configuration file or use fallback defaults.")

        st.markdown("### 📂 File Configuration")
        col_file1, col_file2 = st.columns([3, 1])
        
        default_file_path_key = "default_weight_file_path"
        if default_file_path_key not in st.session_state:
            st.session_state[default_file_path_key] = "data/weight/weight_default.csv"

        with col_file1:
            st.session_state[default_file_path_key] = st.text_input(
                "Weight Data File Path:",
                value=st.session_state[default_file_path_key],
                help="Path to the CSV file containing default weights (columns: 'criterion', 'weight')"
            )
        with col_file2:
            st.write("")
            st.write("")
            if st.button("🔄 Load Default Weights", type="primary", use_container_width=True):
                with st.spinner("Loading default weights..."):
                    loaded_weights = load_default_weights(st.session_state[default_file_path_key])
                    if loaded_weights:
                        st.session_state.weights = loaded_weights
                        st.success("✅ Default weights loaded successfully!")
                    else:
                        st.error("❌ Failed to load from file. Trying fallback.")
                        st.session_state.weights = load_default_weights("") # Explicitly load fallback
                        if st.session_state.weights:
                             st.info("ℹ️ Using fallback default weights.")
                        else:
                             st.error("❌ Fallback default weights also failed to load.")


        # If no weights are loaded yet (e.g., first time in default mode)
        if not st.session_state.weights:
            st.session_state.weights = load_default_weights(st.session_state[default_file_path_key])
            if not st.session_state.weights: # If file load fails, try fallback
                st.session_state.weights = load_default_weights("")
                if st.session_state.weights and st.session_state.weight_method == 'default': # Show only if relevant
                    st.toast("Loaded fallback default weights.", icon="ℹ️")


        if st.session_state.weights:
            st.markdown("### 📊 Current Default Weights")
            # ... (bagian tampilan default weights tetap sama seperti kode Anda sebelumnya) ...
            weight_col1, weight_col2 = st.columns([2, 1])
            with weight_col1:
                weights_df_display = pd.DataFrame([
                    {
                        'Criterion': criterion,
                        'Weight': weight,
                        'Percentage': f"{weight*100:.1f}%",
                        'Description': criterion_descriptions.get(criterion, 'No description available')
                    }
                    for criterion, weight in st.session_state.weights.items() if criterion in criterion_descriptions
                ])
                st.dataframe(weights_df_display, use_container_width=True, hide_index=True)

                if validate_weights(st.session_state.weights):
                    st.success("✅ Weights are properly normalized (sum = 1.0)")
                else:
                    total = sum(st.session_state.weights.values()) if st.session_state.weights else 0
                    st.warning(f"⚠️ Weights sum to {total:.3f}. Consider normalizing or checking the source file.")
            with weight_col2:
                st.markdown("**📈 Weight Distribution**")
                weights_for_chart_data = {
                    k.replace('C', '').replace('_', ' '): v 
                    for k, v in st.session_state.weights.items() if k in criterion_descriptions
                }
                if weights_for_chart_data:
                    weights_for_chart = pd.DataFrame(list(weights_for_chart_data.items()), columns=['Criterion', 'Weight'])
                    
                    weights_values = [v for k,v in st.session_state.weights.items() if k in criterion_descriptions]
                    if weights_values:
                        st.metric("Highest Weight", f"{max(weights_values):.3f}")
                        st.metric("Lowest Weight", f"{min(weights_values):.3f}")
                        st.metric("Average Weight", f"{np.mean(weights_values):.3f}")
                else:
                    st.caption("No valid weights to display in chart.")
        else:
            st.warning("No default weights currently loaded.")

    else:  # custom weights
        st.subheader("🎛️ Custom Weights Configuration")
        st.info("🎯 **Custom Weights Mode**: Manually adjust the importance of each criterion using selection boxes (1 = Least Important, 5 = Most Important). Weights should be normalized to sum to 1.0 for proper analysis.")

        if set(st.session_state.raw_custom_ratings.keys()) != set(criteria_list):
            current_raw_ratings = st.session_state.raw_custom_ratings.copy()
            st.session_state.raw_custom_ratings = {c: current_raw_ratings.get(c, 3) for c in criteria_list}

        st.markdown("### ⚖️ Adjust Criterion Importance Ratings")
        st.markdown("*Use the selection boxes below to set the importance rating for each criterion (1 = Least Important, 5 = Most Important)*")

        # Store a copy of raw_custom_ratings from *before* rendering UI elements for comparison
        ratings_before_ui = st.session_state.raw_custom_ratings.copy()
        
        temp_raw_ratings_from_ui = {}
        mid_point = len(criteria_list) // 2
        rating_options = [1, 2, 3, 4, 5]

        # Create two columns for User input
        input_col1, input_col2 = st.columns(2)
        with input_col1:
            st.markdown("**Criteria 1-5**")
            for criterion in criteria_list[:mid_point]:
                temp_raw_ratings_from_ui[criterion] = st.selectbox(
                    label=f"{re.sub(r'C[0-9]+', '', criterion).replace('_', ' ')}:",
                    options=rating_options,
                    index=rating_options.index(st.session_state.raw_custom_ratings.get(criterion, 3)),
                    help=criterion_descriptions[criterion],
                    key=f"select_{criterion}"
                )
                st.caption(criterion_descriptions[criterion])
        with input_col2:
            st.markdown("**Criteria 6-10**")
            for criterion in criteria_list[mid_point:]:
                temp_raw_ratings_from_ui[criterion] = st.selectbox(
                    # use regular expression to format criterion name
                    label=f"{re.sub(r'C[0-9]+', '', criterion).replace('_', ' ')}:",
                    options=rating_options,
                    index=rating_options.index(st.session_state.raw_custom_ratings.get(criterion, 3)),
                    help=criterion_descriptions[criterion],
                    key=f"select_{criterion}"
                )
                st.caption(criterion_descriptions[criterion])
        
        st.session_state.raw_custom_ratings = temp_raw_ratings_from_ui.copy()

        # If user changed any raw rating, then previous normalization (if any) is invalid
        if ratings_before_ui != st.session_state.raw_custom_ratings:
            st.session_state.custom_weights_are_normalized = False

        # Update st.session_state.weights for display based on normalization flag
        if not st.session_state.custom_weights_are_normalized:
            st.session_state.weights = st.session_state.raw_custom_ratings.copy()
        # Else: st.session_state.weights should already hold the normalized values from previous step

        st.markdown("---")
        st.markdown("### 📊 Weight Summary & Validation")
        
        current_weights_for_summary = st.session_state.weights
        total_weight_val = sum(current_weights_for_summary.values()) if current_weights_for_summary else 0

        summary_col1, summary_col2, summary_col3 = st.columns([2, 1, 1])
        with summary_col1:
            st.markdown("**Current Weight Values**")
            # ... (logika dataframe summary tetap sama seperti kode Anda sebelumnya, pastikan menggunakan current_weights_for_summary) ...
            summary_df_data = []
            for criterion, weight_val in current_weights_for_summary.items():
                is_raw_rating = isinstance(weight_val, int) and weight_val in rating_options and not st.session_state.custom_weights_are_normalized
                display_weight = f"{weight_val}" if is_raw_rating else f"{weight_val:.3f}"
                
                # Calculate percentage
                if st.session_state.custom_weights_are_normalized : # If normalized, percentage is weight * 100
                    percentage = f"{weight_val * 100:.1f}%"
                elif total_weight_val > 0 : # If raw and total is not zero, calculate relative percentage
                    percentage = f"{(weight_val / total_weight_val * 100):.1f}% (raw)"
                else: # Raw and total is zero
                    percentage = "0.0% (raw)"

                summary_df_data.append({
                    'Criterion': criterion,
                    'Value/Weight': display_weight,
                    'Percentage': percentage
                })
            summary_df = pd.DataFrame(summary_df_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)


        with summary_col2:
            # ... (logika chart tetap sama, gunakan current_weights_for_summary) ...
            st.markdown("**📈 Visualization**")
            weights_for_chart_data = {
                k.replace('C', '').replace('_', ' '): v 
                for k, v in current_weights_for_summary.items()
            }
            if weights_for_chart_data:
                weights_for_chart = pd.DataFrame(list(weights_for_chart_data.items()), columns=['Criterion', 'Weight'])
                st.bar_chart(weights_for_chart.set_index('Criterion'), height=250)
            else:
                st.caption("No data for chart.")


        with summary_col3:
            st.markdown("**📊 Statistics**")
            # ... (logika metric tetap sama, gunakan current_weights_for_summary dan total_weight_val) ...
            # status_normalized = validate_weights(current_weights_for_summary) # OLD way
            status_normalized = st.session_state.custom_weights_are_normalized # NEW way using flag

            if status_normalized: # Check our flag
                st.metric("Total Normalized Weight", f"{total_weight_val:.3f}")
                st.metric("Total Percentage", f"{total_weight_val*100:.1f}%")
                st.success("✅ Normalized")
            else:
                st.metric("Sum of Ratings", f"{int(total_weight_val)}") # Show sum of 1-5
                st.warning("⚠️ Not Normalized")
            
            weights_values_list = list(current_weights_for_summary.values()) if current_weights_for_summary else []
            if weights_values_list:
                st.metric("Highest", f"{max(weights_values_list):.3f}")
                st.metric("Lowest", f"{min(weights_values_list):.3f}")
                st.metric("Average", f"{np.mean(weights_values_list):.3f}")

        # Normalization section
        if not st.session_state.custom_weights_are_normalized: # Show if flag is False
            st.markdown("### 🔄 Weight Normalization")
            st.warning(f"⚠️ Current sum of ratings is {int(total_weight_val)}. For proper analysis, weights should sum to 1.0.")
            
            norm_col1, norm_col2 = st.columns([1, 3])
            with norm_col1:
                if st.button("🔄 Normalize Weights", type="primary", use_container_width=True):
                    normalized_weights = normalize_weights(st.session_state.raw_custom_ratings)
                    st.session_state.weights = normalized_weights
                    st.session_state.custom_weights_are_normalized = True # SET FLAG
                    st.success("✅ Weights have been normalized!")
                    st.rerun()
            with norm_col2:
                st.info("Normalization will proportionally adjust all ratings so they sum to exactly 1.0.")
    
    # Action buttons section
    st.markdown("---")
    # ... (tombol actions tetap sama, pastikan mereka menggunakan st.session_state.weights dan mungkin memeriksa st.session_state.custom_weights_are_normalized jika relevan, misal untuk "Save") ...
    button_col1, button_col2 = st.columns(2)

    with button_col1:
        if st.button("💾 Save Weights", type="primary", use_container_width=True):
            if st.session_state.weights:
                # Check if custom weights are unnormalized before saving
                if st.session_state.weight_method == 'custom' and not st.session_state.custom_weights_are_normalized:
                    st.warning("⚠️ Saving unnormalized custom ratings. Consider normalizing first.")
                # Here you would typically save to database or file
                st.success("✅ Weights saved successfully! (simulation)")
            else:
                st.error("❌ No weights to save")

    with button_col2:
        if st.button("➡️ Continue", type="primary", use_container_width=True):
            # For "Continue", weights MUST be normalized (sum to 1)
            is_valid_for_continue = validate_weights(st.session_state.weights)
            # Additionally, if in custom mode, ensure our flag also says it's normalized
            if st.session_state.weight_method == 'custom':
                is_valid_for_continue = is_valid_for_continue and st.session_state.custom_weights_are_normalized

            if st.session_state.weights and is_valid_for_continue:
                st.success("✅ Proceeding to analysis with current weights...")
            elif not st.session_state.weights:
                 st.error("❌ No weights configured. Please set weights first.")
            else: 
                st.error("❌ Please ensure custom weights are normalized (sum to 1.0) before continuing.")