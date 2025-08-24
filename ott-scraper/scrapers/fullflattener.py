import streamlit as st
import pandas as pd
import io

# ---------------- STREAMLIT APP ---------------- #
st.set_page_config(page_title="Poster Grouper", layout="wide")

st.title("🎯 Poster Grouper (Flattened → Grouped)")
st.markdown("Upload a flattened Excel (Title + SeasonPoster rows) to group poster links back per Title.")

uploaded_file = st.file_uploader("📂 Upload Flattened Excel", type=["xlsx"])

if uploaded_file and st.button("🚀 Group Posters"):
    try:
        # Load Excel
        df = pd.read_excel(uploaded_file)

        # Ensure order is preserved
        df['Title_order'] = df['Title'].factorize()[0]

        # Group SeasonPoster links per Title without sorting
        grouped_df = (
            df.groupby(['Title', 'Title_order'], sort=False)['SeasonPoster']
              .apply(lambda x: ",".join(x.astype(str)))
              .reset_index()
              .drop(columns=['Title_order'])
        )

        # Show result preview
        st.success("✅ Grouping complete!")
        st.dataframe(grouped_df)

        # Prepare Excel for download
        buffer = io.BytesIO()
        grouped_df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "⬇ Download Grouped Excel",
            buffer,
            file_name="poster_grouped.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
