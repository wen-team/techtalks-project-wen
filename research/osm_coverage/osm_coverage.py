"""PW-5: Check OpenStreetMap coverage of landmarks in 3 target areas.

1. Downloads named places (churches, pharmacies, shops...) around each area.
2. Counts them, and how many have an Arabic name.
3. Checks which landmarks from real address descriptions exist in OSM.
"""

import pandas as pd
import osmnx as ox
from rapidfuzz import fuzz, process

ox.settings.use_cache = True  # don't download the same area twice

# Centre of each area and radius in metres
AREAS = {
    "Hamra": (33.8963, 35.4823),
    "Jdeideh": (33.8921, 35.5606),
    "Jounieh": (33.9808, 35.6178),
}
RADIUS_M = 2000

# Kinds of places people use as landmarks
TAGS = {
    "amenity": True,
    "shop": True,
    "tourism": True,
    "historic": True,
    "leisure": True,
    "office": True,
    "healthcare": True,
}

NAME_COLUMNS = ["name", "name:ar", "name:en", "alt_name"]
MATCH_THRESHOLD = 80  # 0-100, how similar a name must be to count as found


def category(row):
    """First tag that describes the place, e.g. 'amenity=pharmacy'."""
    for key in TAGS:
        value = row.get(key)
        if isinstance(value, str):
            return f"{key}={value}"
    return "other"


def download_landmarks(area, centre):
    print(f"Downloading {area}...")
    gdf = ox.features_from_point(centre, tags=TAGS, dist=RADIUS_M)
    gdf = gdf[gdf.get("name").notna()]  # keep only places with a name

    points = gdf.geometry.representative_point()
    table = pd.DataFrame({
        "area": area,
        "name": gdf["name"],
        "name_ar": gdf.get("name:ar"),
        "name_en": gdf.get("name:en"),
        "alt_name": gdf.get("alt_name"),
        "brand": gdf.get("brand"),                      ##############
        "category": gdf.apply(category, axis=1),
        "lat": points.y,
        "lon": points.x,
    }).reset_index(drop=True)
    return table


def all_names(table):
    """Every name of every landmark, lowercased, for fuzzy matching."""
    names = []
    for col in ["name", "name_ar", "name_en", "alt_name", "brand"]:     ############
        names += table[col].dropna().astype(str).str.lower().tolist()
        return [n for n in names if len(n) >= 3]  # ignore 1-2 letter names


def main():
    landmarks = pd.concat(
        [download_landmarks(area, centre) for area, centre in AREAS.items()],
        ignore_index=True,
    )
    landmarks.to_csv("landmarks.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved {len(landmarks)} landmarks to landmarks.csv\n")

    # 1. How many named places, and how many with an Arabic name
    summary = landmarks.groupby("area").agg(
        landmarks=("name", "count"),
        with_arabic_name=("name_ar", "count"),
    )
    summary["arabic_%"] = (100 * summary["with_arabic_name"] / summary["landmarks"]).round(0)
    print(summary, "\n")

    # 2. Most common kinds of places
    print(landmarks["category"].value_counts().head(10), "\n")

    # 3. Landmarks mentioned in real descriptions: are they in OSM?
    mentions = pd.read_csv("mentions.csv", encoding="utf-8")
    results = []
    for _, row in mentions.iterrows():
        names = all_names(landmarks[landmarks["area"] == row["area"]])
        best = process.extractOne(str(row["mention"]).lower(), names, scorer=fuzz.token_set_ratio)
        found = best is not None and best[1] >= MATCH_THRESHOLD
        results.append({
            "area": row["area"],
            "mention": row["mention"],
            "best_match": best[0] if best else "",
            "score": round(best[1]) if best else 0,
            "found": found,
        })
    results = pd.DataFrame(results)
    results.to_csv("mention_results.csv", index=False, encoding="utf-8-sig")
    print(results.to_string(index=False), "\n")

    coverage = results.groupby("area")["found"].mean().mul(100).round(0)
    print("Coverage of mentioned landmarks (%):")
    print(coverage)
    print(f"\nOverall: {results['found'].mean() * 100:.0f}% of mentioned landmarks found in OSM")


if __name__ == "__main__":
    main()