# flattener.py
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Excel Flattener", layout="centered")

st.title("📂 Excel Season Posters Flattener")
st.write("Upload an Excel file with `Title` and `Season Posters` columns. "
         "This tool will flatten multiple poster URLs into separate rows.")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # --- Validation ---
        if not {"Title", "Season Posters"}.issubset(df.columns):
            st.error("❌ Your Excel must have 'Title' and 'Season Posters' columns.")
        else:
            st.success("✅ File uploaded successfully!")

            # --- Flatten Logic ---
            def flatten_posters(row):
                posters = str(row["Season Posters"]).split(",")
                return [{"Title": row["Title"], "Poster": p.strip()} for p in posters if p.strip()]

            flat_data = []
            for _, row in df.iterrows():
                flat_data.extend(flatten_posters(row))

            flat_df = pd.DataFrame(flat_data)

            st.subheader("📊 Preview of Flattened Data")
            st.dataframe(flat_df.head(20))

            # --- Download Section ---
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                flat_df.to_excel(writer, index=False, sheet_name="Flattened")
            output.seek(0)

            st.download_button(
                label="📥 Download Flattened Excel",
                data=output,
                file_name="flattened_season_posters.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"⚠️ Error processing file: {e}")
else:
    st.info("⬆️ Please upload an Excel file to continue.")
