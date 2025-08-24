import pandas as pd
import json
import re

def safe_int(value, default=0):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def parse_seasons(season_str, posters_str):
    seasons = []
    posters = [p.strip() for p in str(posters_str).split(",") if p.strip() and p.strip().lower() != "not found"]

    for idx, item in enumerate(str(season_str).split(",")):
        item = item.strip()
        season_number, episodes_count = 0, 0

        match = re.match(r"Season\s*(\d+)\s*:\s*(\d+)", item, re.IGNORECASE)
        if match:
            season_number = safe_int(match.group(1))
            episodes_count = safe_int(match.group(2))
        else:
            num_match = re.search(r"(\d+)", item)
            season_number = safe_int(num_match.group(1)) if num_match else 0
            episodes_count = 0

        poster_url = posters[idx] if idx < len(posters) else ""
        if not poster_url or "https://res.cloudinary.com/" not in poster_url:
            poster_url = "data:image/gif;base64"

        seasons.append({
            "season_number": season_number,
            "episodes_count": episodes_count,
            "poster_url": poster_url
        })

    return seasons

def parse_caster(caster_str):
    if not isinstance(caster_str, str) or not caster_str.strip():
        return []

    casters = []
    for part in re.split(r"[|,]", caster_str):
        part = part.strip()
        if not part:
            continue

        actor, role = "", ""
        if " - " in part:
            actor, role = part.split(" - ", 1)
        elif ":" in part:
            actor, role = part.split(":", 1)
        elif " as " in part.lower():
            actor, role = part.split(" as ", 1)
        else:
            actor, role = part, ""

        casters.append({"actor": actor.strip(), "role": role.strip()})
    return casters

def row_to_json(row):
    title = row.get("title", "")
    original_title = row.get("original title", "") or title
    main_poster = row.get("main poster", "").strip()
    if not main_poster or "https://res.cloudinary.com/" not in main_poster:
        main_poster = "data:image/gif;base64"

    return {
        "title": title,
        "Year": safe_int(row.get("year", 0)),
        "original_title": original_title,
        "main_poster": main_poster,
        "seasons_count": safe_int(row.get("seasons count", 0)),
        "season_details": parse_seasons(row.get("season details", ""), row.get("season poster", "")),
        "justwatch_rating": row.get("justwatch rating", ""),
        "imdb_rating": float(row.get("imdb rating", 0)) if str(row.get("imdb rating", "")).replace(".", "", 1).isdigit() else 0,
        "rotten_tomatoes": row.get("rotten tomatoes", ""),
        "genres": [g.strip() for g in str(row.get("genres", "")).split(",") if g.strip()],
        "runtime": row.get("runtime", ""),
        "production_country": row.get("production country", ""),
        "description": row.get("description", ""),
        "youtube_links": [link.strip() for link in str(row.get("youtube links", "")).split(",") if link.strip()],
        "caster": parse_caster(row.get("caster", "")),
        "platform": "hotstar"
    }

def excel_to_json(input_file, output_file):
    df = pd.read_excel(input_file)
    df = df.fillna("")
    df.columns = df.columns.str.strip().str.lower()

    data = [row_to_json(row) for _, row in df.iterrows()]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
