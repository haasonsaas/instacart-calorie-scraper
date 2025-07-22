
"""
instacart_calorie_scraper.py
--------------------------------
Ingest Instacart product JSON dumps (Target / Safeway / Costco) and auto‑populate
a unified CSV with:
    * Store
    * Product name
    * Aisle / location
    * Price (USD, float)
    * Calories_per_serving (float, or 'N/A')

Calorie data source priority:
    1. OpenFoodFacts search API (free, no key required).
    2. USDA FoodData Central API (optional, requires API key in env USDA_API_KEY).

Run:
    python instacart_calorie_scraper.py --targets /path/products_target.json \
                                        --safeway /path/products_safeway.json \
                                        --costco /path/products_costco.json \
                                        --out instacart_with_calories.csv

Dependencies:
    requests, pandas (pip install requests pandas)
"""

import argparse, json, os, re, sys, time
from typing import Dict, Any, List, Optional

import requests
import pandas as pd

HEADERS = {"User-Agent": "InstacartCalorieBot/0.1 (https://github.com/your-repo)"}
OFF_BASE = "https://world.openfoodfacts.org/cgi/search.pl"
FDC_API_BASE = "https://api.nal.usda.gov/fdc/v1/foods/search"
FDC_KEY = os.getenv("USDA_API_KEY")  # Optional

def load_items(store_name: str, path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as fh:
        data = json.load(fh)
    Items = []
    for item in data:
        price_match = re.search(r"[\d\.]+", item.get("price", ""))
        price = float(price_match.group()) if price_match else None
        Items.append(
            {
                "Store": store_name,
                "Name": item.get("name", "").strip(),
                "Location": item.get("location", ""),
                "Price_USD": price,
            }
        )
    return Items

def is_food(name: str) -> bool:
    non_food_keywords = [
        "cat litter",
        "eye drops",
        "dryer sheets",
        "detergent",
        "bandages",
        "batteries",
        "trash bags",
        "foil",
        "wrap",
        "paper towel",
        "toilet paper",
        "tissue",
        "stamp",
        "air freshener",
        "wipe",
        "sunscreen",
        "hand sanitizer",
        "dish soap",
        "laundry",
    ]
    lowered = name.lower()
    return not any(kw in lowered for kw in non_food_keywords)

def calories_from_off(search_term: str) -> Optional[float]:
    params = {
        "search_terms": search_term,
        "json": 1,
        "page_size": 1,
        "fields": "nutriments",
    }
    try:
        resp = requests.get(OFF_BASE, params=params, headers=HEADERS, timeout=9)
        resp.raise_for_status()
        data = resp.json()
        prods = data.get("products", [])
        if not prods:
            return None
        nutriments = prods[0].get("nutriments", {})
        kcal = nutriments.get("energy-kcal_serving") or nutriments.get("energy-kcal_100g")
        if kcal:
            return float(kcal)
    except Exception as e:
        return None
    return None

def calories_from_fdc(search_term: str) -> Optional[float]:
    if not FDC_KEY:
        return None
    params = {"query": search_term, "pageSize": 1, "api_key": FDC_KEY}
    try:
        resp = requests.get(FDC_API_BASE, params=params, headers=HEADERS, timeout=9)
        resp.raise_for_status()
        data = resp.json()
        foods = data.get("foods", [])
        if not foods:
            return None
        for nutrient in foods[0].get("foodNutrients", []):
            if nutrient.get("nutrientName") == "Energy" and nutrient.get("unitName") == "KCAL":
                return nutrient.get("value")
    except Exception:
        return None
    return None

def get_calories(name: str) -> Optional[float]:
    # 1. OpenFoodFacts
    kcal = calories_from_off(name)
    if kcal:
        return kcal
    # 2. USDA FDC
    kcal = calories_from_fdc(name)
    return kcal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True)
    ap.add_argument("--safeway", required=True)
    ap.add_argument("--costco", required=True)
    ap.add_argument("--out", default="instacart_with_calories.csv")
    args = ap.parse_args()

    items = []
    items.extend(load_items("Target", args.targets))
    items.extend(load_items("Safeway", args.safeway))
    items.extend(load_items("Costco", args.costco))

    for itm in items:
        name = itm["Name"]
        if is_food(name):
            kcal = get_calories(name)
            itm["Calories_per_serving"] = kcal if kcal is not None else "Unknown"
        else:
            itm["Calories_per_serving"] = "N/A"

        # polite scrape
        time.sleep(0.5)

    df = pd.DataFrame(items)
    df.sort_values(["Store", "Name"], inplace=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {args.out} with {len(df)} rows.")


if __name__ == "__main__":
    main()
