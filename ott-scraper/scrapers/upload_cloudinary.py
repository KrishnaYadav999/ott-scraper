import streamlit as st
import pandas as pd
import io
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ---------------- LOAD ENV & CONFIGURE CLOUDINARY ---------------- #
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

st.title("☁️ Excel Poster → Cloudinary Uploader")

# ---------------- STREAMLIT FILE UPLOADER ---------------- #
uploaded_file = st.file_uploader(
    "📂 Upload Excel with 'Title' and 'SeasonPoster'",
    type=["xlsx"]
)

def upload_to_cloudinary(url, folder="jio_images/"):
    """Upload an image/video URL to Cloudinary"""
    try:
        res = cloudinary.uploader.upload(url, folder=folder)
        return res.get("secure_url", url)
    except Exception as e:
        st.warning(f"⚠️ Failed to upload {url}: {e}")
        return url

if uploaded_file and st.button("🚀 Upload to Cloudinary"):
    try:
        df = pd.read_excel(uploaded_file)

        # Check required columns
        if not {"Title", "SeasonPoster"}.issubset(df.columns):
            st.error("❌ Excel must have 'Title' and 'SeasonPoster' columns.")
        else:
            expanded_rows = []
            progress = st.progress(0)
            total = len(df)

            for i, (_, row) in enumerate(df.iterrows()):
                title = row["Title"]
                posters = str(row["SeasonPoster"]).split(",")
                posters = [p.strip() for p in posters if p.strip()]

                for poster_url in posters:
                    cloud_url = upload_to_cloudinary(poster_url)
                    expanded_rows.append({"Title": title, "SeasonPoster": cloud_url})

                progress.progress((i + 1) / total)

            # Result DataFrame
            result_df = pd.DataFrame(expanded_rows)
            st.success("✅ Upload complete!")
            st.dataframe(result_df.head(20))

            # Prepare Excel download
            buffer = io.BytesIO()
            result_df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                "⬇ Download Updated Excel",
                buffer,
                file_name="cloudinary_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    except Exception as e:
        st.error(f"❌ Error: {e}")
