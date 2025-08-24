import requests
from bs4 import BeautifulSoup
import re

# --- Helper functions ---
def get_text(soup, selector):
    """Safe text extraction by CSS selector."""
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else None

def upgrade_image_url(url, size="s592", ext=".jpg"):
    """Upgrade JustWatch image URL to higher resolution and set format."""
    if not url:
        return None
    base_url = url.split("?")[0]
    upgraded_url = re.sub(r"/s\d+/", f"/{size}/", base_url)
    if not upgraded_url.endswith(ext):
        upgraded_url = upgraded_url + ext
    return upgraded_url

# --- Main scraping function ---
def scrape_justwatch(url: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        )
    }
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return {"Error": f"Failed to fetch {url}"}

    soup = BeautifulSoup(res.text, "html.parser")

    # --- Title & Year ---
    title, year = None, None
    title_year = soup.select_one("h1.title-detail-hero__details__title")
    if title_year:
        title_text = title_year.get_text(" ", strip=True)
        match = re.match(r"(.*?)\s+\((\d{4})\)", title_text)
        title = match.group(1) if match else title_text
        year = match.group(2) if match else None

    # --- Original title ---
    original_title = get_text(soup, "h3.original-title")

    # --- Main Poster ---
    main_poster_url = None
    main_poster_tag = soup.select_one(".title-poster__image img")
    if main_poster_tag:
        src = main_poster_tag.get("src") or main_poster_tag.get("data-src")
        main_poster_url = upgrade_image_url(src)

    # --- Seasons ---
    seasons_data = []
    for season in soup.select("#season-list .season-card"):
        season_name = get_text(season, ".season-number")
        episodes = get_text(season, ".episodes-number")
        if season_name and episodes:
            seasons_data.append(f"{season_name} : {episodes}")
    season_details_str = ", ".join(seasons_data) if seasons_data else None

    # --- Ratings ---
    jw_rating, imdb_rating, rt_rating = None, None, None
    for rating in soup.select(".jw-scoring-listing__rating"):
        text = rating.get_text(strip=True)
        img = rating.select_one("img")
        alt = img.get("alt", "").lower() if img else ""

        # JustWatch rating
        if "justwatch" in alt or "jw" in text.lower():
            jw_rating = re.search(r"[\d.]+", text)
            jw_rating = jw_rating.group(0) if jw_rating else text

        # IMDb rating
        elif "imdb" in alt or "imdb" in text.lower():
            imdb_rating = re.search(r"[\d.]+", text)
            imdb_rating = imdb_rating.group(0) if imdb_rating else text

        # Rotten Tomatoes (🍅, tomatometer, rotten)
        elif (
            "rotten" in alt
            or "tomato" in alt
            or "rotten" in text.lower()
            or "tomato" in text.lower()
            or "tomatometer" in text.lower()
            or "🍅" in text
        ):
            rt_rating_match = re.search(r"\d+%", text)
            if rt_rating_match:
                rt_rating = rt_rating_match.group(0)
            else:
                rt_rating = text

    # --- Genres ---
    genres = ",".join(
        [
            g.get_text(strip=True)
            for g in soup.select(
                ".poster-detail-infos__value span, "
                ".poster-detail-infos__value a"
            )
        ]
    )

    # --- Runtime ---
    runtime = get_text(soup, "h3:-soup-contains('Runtime') + .poster-detail-infos__value")

    # --- Age rating ---
    age_rating = get_text(soup, "h3:-soup-contains('Age rating') + .poster-detail-infos__value")

    # --- Production country ---
    prod_country = get_text(soup, "h3:-soup-contains('Production country') + .poster-detail-infos__value")

    # --- Synopsis ---
    synopsis = get_text(soup, "#synopsis p")

    # --- YouTube trailer links ---
    youtube_links = []
    for img in soup.select("#clips_trailers img"):
        src = img.get("src", "")
        match = re.search(r"vi/([^/]+)/", src)
        if match:
            youtube_links.append(f"https://www.youtube.com/watch?v={match.group(1)}")

    # --- Final dictionary ---
    return {
        "Title": title,
        "Year": year,
        "Original Title": original_title,
        "Main Poster": main_poster_url,
        "Seasons Count": len(seasons_data),
        "Season Details": season_details_str,
        "JustWatch Rating": jw_rating,
        "IMDB Rating": imdb_rating,
        "Rotten Tomatoes": rt_rating,
        "Genres": genres,
        "Runtime": runtime,
        "Age Rating": age_rating,
        "Production Country": prod_country,
        "Synopsis": synopsis,
        "YouTube Links": ", ".join(youtube_links),
        "Source URL": url,
    }
