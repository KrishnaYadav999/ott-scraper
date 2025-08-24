import streamlit as st
import pandas as pd
import json
import io
import cloudinary
import cloudinary.uploader

from scrapers.justwatch import scrape_justwatch
from scrapers.poster_selenium import scrape_posters_with_selenium
from scrapers.excel_to_json import row_to_json
from scrapers.cast_scraper import scrape_cast_from_excel   # ✅ NEW import


# ---------------- STREAMLIT APP ---------------- #
st.set_page_config(page_title="OTT Scraper", layout="wide")

st.sidebar.title("📌 Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Home",
        "🎬 JustWatch Scraper",
        "🖼 Poster Scraper (Selenium)",
        "🧑‍🎤 Cast Scraper",
        "📑 Excel → JSON Converter",
        "🪄 Excel Flattener",
        "🔗 Poster Grouper",        # ✅ NEW
        "☁️ Cloudinary Uploader",   # ✅
    ]
)


# ---------------- HOME ---------------- #
if page == "🏠 Home":
    st.title("🎥 OTT Scraper Dashboard")
    st.markdown("Welcome! Use the sidebar to navigate between tools.")


# ---------------- JUSTWATCH SCRAPER ---------------- #
elif page == "🎬 JustWatch Scraper":
    st.title("🎬 JustWatch Scraper")
    uploaded_file = st.file_uploader("📂 Upload Excel with URLs", type=["xlsx"])

    if uploaded_file and st.button("🚀 Start Scraping"):
        df_urls = pd.read_excel(uploaded_file)
        url_column = [col for col in df_urls.columns if "url" in col.lower()][0]

        scraped_data = []
        progress = st.progress(0)

        urls = df_urls[url_column].dropna().tolist()
        for i, url in enumerate(urls):
            scraped_data.append(scrape_justwatch(url))
            progress.progress((i + 1) / len(urls))

        df_output = pd.DataFrame(scraped_data)
        st.success("✅ Scraping completed!")
        st.dataframe(df_output)

        buffer = io.BytesIO()
        df_output.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            "⬇ Download Excel",
            buffer,
            file_name="justwatch_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ---------------- POSTER SCRAPER ---------------- #
elif page == "🖼 Poster Scraper (Selenium)":
    st.title("🖼 Poster Scraper (Selenium)")
    uploaded_file = st.file_uploader("📂 Upload Excel with 'Source URL'", type=["xlsx"])

    if uploaded_file and st.button("🚀 Start Poster Scraping"):
        df_result = scrape_posters_with_selenium(uploaded_file)
        if df_result is not None:
            st.success("✅ Poster scraping complete!")
            st.dataframe(df_result)

            buffer = io.BytesIO()
            df_result.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                "⬇ Download Excel",
                buffer,
                file_name="poster_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# ---------------- CAST SCRAPER ---------------- #
elif page == "🧑‍🎤 Cast Scraper":
    st.title("🧑‍🎤 Cast Scraper")
    uploaded_file = st.file_uploader("📂 Upload Excel with 'Source URL'", type=["xlsx"])

    if uploaded_file and st.button("🚀 Start Cast Scraping"):
        input_path = "temp_cast_input.xlsx"
        output_path = "temp_cast_output.xlsx"

        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df_result = None
        try:
            scrape_cast_from_excel(input_path, output_path)
            df_result = pd.read_excel(output_path)
        except Exception as e:
            st.error(f"⚠️ Error: {e}")

        if df_result is not None:
            st.success("✅ Cast scraping complete!")
            st.dataframe(df_result)

            buffer = io.BytesIO()
            df_result.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                "⬇ Download Excel",
                buffer,
                file_name="cast_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# ---------------- EXCEL TO JSON ---------------- #
elif page == "📑 Excel → JSON Converter":
    st.title("📑 Excel to JSON Converter")
    uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])

    if uploaded_file and st.button("🚀 Convert to JSON"):
        df = pd.read_excel(uploaded_file)
        df = df.fillna("")
        df.columns = df.columns.str.strip().str.lower()

        data = [row_to_json(row) for _, row in df.iterrows()]

        json_str = json.dumps(data, ensure_ascii=False, indent=4)

        st.success("✅ Conversion complete!")
        st.json(data[:2])  # preview

        st.download_button(
            "⬇ Download JSON",
            json_str.encode("utf-8"),
            file_name="output.json",
            mime="application/json",
        )


# ---------------- EXCEL FLATTENER ---------------- #
elif page == "🪄 Excel Flattener":
    st.title("🪄 Excel Season Posters Flattener")
    uploaded_file = st.file_uploader("📂 Upload Excel with 'Title' and 'Season Posters'", type=["xlsx"])

    if uploaded_file and st.button("🚀 Flatten Excel"):
        try:
            df = pd.read_excel(uploaded_file)

            if not {"Title", "Season Posters"}.issubset(df.columns):
                st.error("❌ Excel must have 'Title' and 'Season Posters' columns.")
            else:
                expanded_rows = []
                for _, row in df.iterrows():
                    posters = str(row["Season Posters"]).split(",")
                    posters = [p.strip() for p in posters if p.strip()]
                    for poster in posters:
                        expanded_rows.append({"Title": row["Title"], "SeasonPoster": poster})

                flat_df = pd.DataFrame(expanded_rows)

                st.success("✅ Flattening complete!")
                st.dataframe(flat_df.head(20))

                buffer = io.BytesIO()
                flat_df.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)

                st.download_button(
                    "⬇ Download Flattened Excel",
                    buffer,
                    file_name="flattened_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except Exception as e:
            st.error(f"⚠️ Error: {e}")


# ---------------- POSTER GROUPER ---------------- #
elif page == "🔗 Poster Grouper":
    st.title("🔗 Poster Grouper (Flattened → Grouped)")
    uploaded_file = st.file_uploader("📂 Upload Flattened Excel", type=["xlsx"])

    if uploaded_file and st.button("🚀 Group Posters"):
        try:
            df = pd.read_excel(uploaded_file)
            df['Title_order'] = df['Title'].factorize()[0]

            grouped_df = (
                df.groupby(['Title', 'Title_order'], sort=False)['SeasonPoster']
                  .apply(lambda x: ",".join(x.astype(str)))
                  .reset_index()
                  .drop(columns=['Title_order'])
            )

            st.success("✅ Grouping complete!")
            st.dataframe(grouped_df)

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


# ---------------- CLOUDINARY UPLOADER ---------------- #
elif page == "☁️ Cloudinary Uploader":
    st.title("☁️ Excel Poster → Cloudinary Uploader")
    uploaded_file = st.file_uploader("📂 Upload Excel with 'Title' and 'SeasonPoster'", type=["xlsx"])

    if uploaded_file and st.button("🚀 Upload to Cloudinary"):
        try:
            df = pd.read_excel(uploaded_file)

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
                        try:
                            upload_result = cloudinary.uploader.upload(
                                poster_url,
                                folder="jio_images/"
                            )
                            cloud_url = upload_result.get("secure_url", poster_url)
                            expanded_rows.append({"Title": title, "SeasonPoster": cloud_url})
                        except Exception as e:
                            expanded_rows.append({"Title": title, "SeasonPoster": poster_url})
                            st.warning(f"⚠️ Failed for {poster_url}: {e}")

                    progress.progress((i + 1) / total)

                result_df = pd.DataFrame(expanded_rows)

                st.success("✅ Upload complete!")
                st.dataframe(result_df.head(20))

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
