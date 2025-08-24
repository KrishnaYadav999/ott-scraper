import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st
import io

def scrape_posters_with_selenium(uploaded_file, run_headless=False):
    """Scrape Main & Season posters from JustWatch using Selenium."""

    # === Load Excel file into DataFrame ===
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
        return None

    if "Source URL" not in df.columns:
        st.error("❌ Excel must contain a 'Source URL' column.")
        return None

    # Add missing columns
    if "Main Poster" not in df.columns:
        df["Main Poster"] = None
    if "Season Posters" not in df.columns:
        df["Season Posters"] = None

    # === Setup Selenium driver ===
    options = webdriver.ChromeOptions()
    if run_headless:
        options.add_argument("--headless=new")
    else:
        options.add_argument("--start-maximized")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )

    urls = df["Source URL"].dropna().tolist()
    progress = st.progress(0)
    status = st.empty()

    # === Loop through URLs ===
    for idx, url in df["Source URL"].dropna().items():
        status.text(f"Scraping {url} ...")
        try:
            driver.get(url)
            time.sleep(3)

            # ✅ Scroll to force lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # --- MAIN POSTER ---
            try:
                main_poster_el = driver.find_element(By.CSS_SELECTOR, ".title-sidebar__title-with-poster__poster img")
                main_poster = (
                    main_poster_el.get_attribute("src")
                    or main_poster_el.get_attribute("data-src")
                    or main_poster_el.get_attribute("data-srcset")
                )
                if main_poster and main_poster.startswith("data:image"):
                    df.at[idx, "Main Poster"] = "Not Found"
                else:
                    df.at[idx, "Main Poster"] = main_poster
            except:
                df.at[idx, "Main Poster"] = "Not Found"

            # --- SEASON POSTERS ---
            try:
                season_img_elements = driver.find_elements(By.CSS_SELECTOR, ".season-card__link img")
                season_urls = []
                for img in season_img_elements:
                    u = (
                        img.get_attribute("src")
                        or img.get_attribute("data-src")
                        or img.get_attribute("data-srcset")
                    )
                    if u and not u.startswith("data:image"):
                        season_urls.append(u)

                df.at[idx, "Season Posters"] = ", ".join(season_urls) if season_urls else "Not Found"
            except:
                df.at[idx, "Season Posters"] = "Not Found"

        except Exception as e:
            df.at[idx, "Main Poster"] = "Error"
            df.at[idx, "Season Posters"] = "Error"

        # ✅ update progress bar
        progress.progress((list(df["Source URL"].dropna().index).index(idx) + 1) / len(urls))

    driver.quit()
    status.text("✅ Scraping complete!")

    return df


# ================= STREAMLIT APP ==================
def main():
    st.title("🎬 JustWatch Poster Scraper")

    uploaded_file = st.file_uploader("Upload Excel file with 'Source URL' column", type=["xlsx"])
    headless_mode = st.checkbox("Run in headless mode", value=False)

    if uploaded_file:
        if st.button("Start Scraping"):
            df = scrape_posters_with_selenium(uploaded_file, run_headless=headless_mode)
            if df is not None:
                st.success("Scraping finished!")
                st.dataframe(df)

                # Download button
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False)
                st.download_button(
                    label="📥 Download Results",
                    data=output.getvalue(),
                    file_name="scraped_posters.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
