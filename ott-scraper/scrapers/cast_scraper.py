import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_cast_from_excel(input_excel, output_excel, url_column="Source URL"):
    """
    Reads an Excel file, scrapes cast details from each URL, and saves results to a new Excel file.
    """

    # ===== 1. Read Excel file =====
    df = pd.read_excel(input_excel)

    if url_column not in df.columns:
        raise ValueError(f"❌ Column '{url_column}' not found in Excel. Found columns: {list(df.columns)}")

    urls_to_scrape = df[url_column].dropna().unique()  # remove duplicates
    final_data = []

    # ===== 2. Setup Selenium =====
    options = Options()
    options.add_argument("--headless")  # comment out if you want browser visible
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    # ===== 3. Loop through all URLs =====
    for url in urls_to_scrape:
        print(f"🎬 Scraping: {url}")
        try:
            driver.get(url)

            # Wait until cast section loads (10s timeout)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "title-credit-name"))
            )

            # Scroll down to load more elements
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # Keep clicking "Next" button until disabled
            while True:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR,
                                                      ".title-credits__actor-list__navigation--next")
                    if next_button.is_enabled():
                        next_button.click()
                        time.sleep(0.8)
                    else:
                        break
                except:
                    break

            # Extract actors and roles
            actors = driver.find_elements(By.CLASS_NAME, "title-credit-name")
            roles = driver.find_elements(By.CSS_SELECTOR, ".title-credits__actor--role--name strong")

            if actors:
                role_texts = [role.text.strip() if role.text.strip() else "Unknown Role" for role in roles]

                # Ensure matching lengths
                while len(role_texts) < len(actors):
                    role_texts.append("Unknown Role")

                cast_list = [f"{name.text.strip()} - {role}" for name, role in zip(actors, role_texts)]
                cast_text = " | ".join(cast_list)
            else:
                cast_text = "Not Found"

            final_data.append({
                "Source URL": url,
                "Cast": cast_text
            })

        except Exception as e:
            print(f"⚠️ Error scraping {url}: {e}")
            final_data.append({
                "Source URL": url,
                "Cast": "Not Found"
            })

    # ===== 4. Save results =====
    pd.DataFrame(final_data).to_excel(output_excel, index=False)
    driver.quit()

    print(f"✅ Done! Results saved to: {output_excel}")
    return output_excel


# ========= Run standalone ========= #
if __name__ == "__main__":
    input_path = r"C:\Users\Aniket Pc\Downloads\net.xlsx"
    output_path = r"C:\Users\Aniket Pc\Downloads\net_cast_output.xlsx"
    scrape_cast_from_excel(input_path, output_path)
