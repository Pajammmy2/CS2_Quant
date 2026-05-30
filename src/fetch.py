import requests
import time
import csv
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # reads .env from the project root

url = "https://steamcommunity.com/market/priceoverview/"

skins = [
    # AK-47s
    "AK-47 | Redline (Field-Tested)",
    "AK-47 | Fuel Injector (Factory New)",
    "AK-47 | Fuel Injector (Field-Tested)",
    "AK-47 | Midnight Laminate (Factory New)",
    "AK-47 | Midnight Laminate (Field-Tested)",
    "AK-47 | Asiimov (Field-Tested)",
    "AK-47 | The Empress (Factory New)",
    "AK-47 | The Empress (Field-Tested)",
    "AK-47 | Vulcan (Factory New)",
    "AK-47 | Vulcan (Field-Tested)",

    # AWPs
    "AWP | Neo-Noir (Factory New)",
    "AWP | Neo-Noir (Field-Tested)",
    "AWP | Queen's Gambit (Factory New)",
    "AWP | Worm God (Factory New)",
    "AWP | Worm God (Field-Tested)",
    "AWP | Asiimov (Field-Tested)",
    "AWP | Hyper Beast (Factory New)",
    "AWP | Hyper Beast (Field-Tested)",
    "AWP | Wildfire (Factory New)",
    "AWP | Wildfire (Field-Tested)",

    # M4A4 / M4A1-S
    "M4A4 | Howl (Factory New)",
    "M4A4 | Howl (Field-Tested)",
    "M4A1-S | Hyper Beast (Factory New)",
    "M4A1-S | Hyper Beast (Field-Tested)",
    "M4A1-S | Welcome to the Jungle (Factory New)",
    "M4A1-S | Welcome to the Jungle (Field-Tested)",
    "M4A1-S | Printstream (Factory New)",
    "M4A1-S | Printstream (Field-Tested)",

    # USP-S
    "USP-S | Blueprint (Factory New)",
    "USP-S | Blueprint (Field-Tested)",
    "USP-S | Kill Confirmed (Factory New)",
    "USP-S | Kill Confirmed (Field-Tested)",
    "USP-S | Printstream (Factory New)",
    "USP-S | Printstream (Field-Tested)",

    # Glock
    "Glock-18 | Fully Tuned (Factory New)",
    "Glock-18 | Gamma Doppler (Factory New)",
    "Glock-18 | Neo-Noir (Factory New)",
    "Glock-18 | Neo-Noir (Field-Tested)",
    "Glock-18 | Moonrise (Field-Tested)",
    "Glock-18 | Moonrise (Factory New)",

    # Desert Eagle
    "Desert Eagle | Blue Ply (Factory New)",
    "Desert Eagle | Blue Ply (Field-Tested)",
    "Desert Eagle | Mecha Industries (Factory New)",
    "Desert Eagle | Mecha Industries (Field-Tested)",
    "Desert Eagle | Printstream (Factory New)",
    "Desert Eagle | Printstream (Field-Tested)",
    "Desert Eagle | Blaze (Factory New)",

    # Other Pistols
    "Five-SeveN | Hyper Beast (Factory New)",
    "Five-SeveN | Hyper Beast (Field-Tested)",

    # Knives - no FN/FT distinction for vanilla, doppler only FN
    "★ Ursus Knife | Fade (Factory New)",
    "★ Flip Knife | Fade (Factory New)",
    "★ Gut Knife | Slaughter (Factory New)",
    "★ Karambit",
    "★ Skeleton Knife",
    "★ M9 Bayonet",
    "★ Gut Knife",
    "★ Flip Knife",

    # Cases - no wear
    "Fracture Case",
    "Horizon Case",
    "Glove Case",
    "Clutch Case",
    "Chroma Case",
    "Operation Broken Fang Case",
]

cookies = {
    "steamLoginSecure": os.environ["STEAM_LOGIN_SECURE"]
}

CSFLOAT_API_KEY = os.environ["CSFLOAT_API_KEY"]

def clean_price(price_str):
    if price_str == "N/A":
        return "N/A"
    return price_str.replace("$", "").replace(",", "")

def get_current_prices():
    file_exists = os.path.exists("data/raw/prices.csv")
    with open("data/raw/prices.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "skin", "lowest_price", "median_price", "volume"])
        for skin in skins:
            params = {"appid": 730, "currency": 1, "market_hash_name": skin}
            response = requests.get(url, params=params)
            data = response.json()
            if "lowest_price" not in data:
                print(f"{skin} → skipping")
                time.sleep(5)
                continue
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                skin,
                clean_price(data.get("lowest_price", "N/A")),
                clean_price(data.get("median_price", "N/A")),
                data.get("volume", "N/A")
            ]
            writer.writerow(row)
            print(f"{skin} → saved")
            time.sleep(5)

def get_price_history(skin_name):
    response = requests.get(
        "https://steamcommunity.com/market/pricehistory/",
        params={"appid": 730, "currency": 1, "market_hash_name": skin_name},
        cookies=cookies
    )
    return response.json()

def save_history(skin_name, history_data):
    safe_name = skin_name.replace(" ", "_").replace("|", "").replace("★", "star").replace("(", "").replace(")", "").strip()
    filename = f"data/raw/{safe_name}_history.csv"
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["skin", "date", "price", "volume"])
        for entry in history_data:
            writer.writerow([skin_name, entry[0], entry[1], entry[2]])
    print(f"Saved {len(history_data)} rows for {skin_name}")

def get_steam_snapshot(skin_name):
    response = requests.get(
        url,
        params={"appid": 730, "currency": 1, "market_hash_name": skin_name},
        cookies=cookies
    )
    data = response.json()
    return {
        "lowest": clean_price(data.get("lowest_price", "N/A")),
        "median": clean_price(data.get("median_price", "N/A")),
        "volume": data.get("volume", "N/A")
    }

def get_skinport_snapshot(skin_names):
    names_str = ",".join(skin_names)
    response = requests.get(
        "https://api.skinport.com/v1/sales/history",
        params={"app_id": 730, "currency": "USD", "market_hash_name": names_str},
        headers={"Accept-Encoding": "br"}
    )
    results = {}
    for item in response.json():
        results[item["market_hash_name"]] = {
            "avg_24h": item["last_24_hours"]["avg"],
            "median_24h": item["last_24_hours"]["median"],
            "volume_24h": item["last_24_hours"]["volume"],
            "avg_30d": item["last_30_days"]["avg"],
            "median_30d": item["last_30_days"]["median"],
        }
    return results

def get_csfloat_snapshot(skin_name):
    response = requests.get(
        "https://csfloat.com/api/v1/listings",
        params={
            "market_hash_name": skin_name,
            "limit": 10,
            "sort_by": "lowest_price",
            "type": "buy_now"    # add this line
        },
        headers={"Authorization": CSFLOAT_API_KEY}
    )
    data = response.json()
    listings = data.get("data", [])
    if not listings:
        return {"lowest": "N/A", "avg_top10": "N/A"}
    prices = [l["price"] / 100 for l in listings]
    return {
        "lowest": min(prices),
        "avg_top10": round(sum(prices) / len(prices), 2)
    }

def take_snapshot():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = "data/raw/snapshots.csv"
    file_exists = os.path.exists(filename)

    print("Fetching Skinport data...")
    skinport_data = get_skinport_snapshot(skins)
    time.sleep(5)

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "skin",
                "steam_lowest", "steam_median", "steam_volume",
                "skinport_avg_24h", "skinport_median_24h", "skinport_volume_24h", "skinport_avg_30d",
                "csfloat_lowest", "csfloat_avg_top10"
            ])

        for skin in skins:
            print(f"Fetching {skin}...")

            steam = get_steam_snapshot(skin)
            time.sleep(3)

            sp = skinport_data.get(skin, {})

            cf = get_csfloat_snapshot(skin)
            time.sleep(3)

            writer.writerow([
                timestamp, skin,
                steam["lowest"], steam["median"], steam["volume"],
                sp.get("avg_24h"), sp.get("median_24h"), sp.get("volume_24h"), sp.get("avg_30d"),
                cf["lowest"], cf["avg_top10"]
            ])
            print(f"{skin} → saved")

# Skins to pull per-listing data from CSFloat (hedonic model training data).
# Mix of non-pattern skins (float drives price) and pattern/phase skins (seed drives price).
LISTING_SKINS = [
    # --- Non-pattern: float level is the main price driver ---
    "AK-47 | Redline (Field-Tested)",
    "AK-47 | Asiimov (Field-Tested)",
    "AWP | Asiimov (Field-Tested)",
    "AWP | Neo-Noir (Field-Tested)",
    "M4A4 | Howl (Field-Tested)",          # contraband; float matters a lot here
    "M4A1-S | Printstream (Factory New)",
    "M4A1-S | Hyper Beast (Factory New)",
    "M4A1-S | Hyper Beast (Field-Tested)",
    "USP-S | Kill Confirmed (Factory New)",
    "Desert Eagle | Printstream (Factory New)",
    "Desert Eagle | Blaze (Factory New)",

    # --- Pattern-dependent: paint_seed determines blue/gold tile coverage ---
    "AK-47 | Case Hardened (Field-Tested)",
    "★ Karambit | Case Hardened (Field-Tested)",
    "★ Karambit | Fade (Factory New)",      # fade % set by seed
    "★ M9 Bayonet | Fade (Factory New)",
    "★ Flip Knife | Fade (Factory New)",

    # --- Doppler: phase (Ruby, Sapphire, Black Pearl, Phase 1-4) adds huge premiums ---
    "★ Karambit | Doppler (Factory New)",
    "★ M9 Bayonet | Doppler (Factory New)",
    "Glock-18 | Gamma Doppler (Factory New)",
]

# Pattern/phase skins get deeper pagination — rare seeds (blue gems, full fades, Sapphires)
# appear at higher prices and won't show in the cheapest 150 listings.
LISTING_SKINS_DEEP = {
    "AK-47 | Case Hardened (Field-Tested)",
    "★ Karambit | Case Hardened (Field-Tested)",
    "★ Karambit | Fade (Factory New)",
    "★ M9 Bayonet | Fade (Factory New)",
    "★ Flip Knife | Fade (Factory New)",
    "★ Karambit | Doppler (Factory New)",
    "★ M9 Bayonet | Doppler (Factory New)",
}

LISTINGS_FILE = "data/raw/listings.csv"
LISTINGS_HEADERS = [
    "timestamp", "market_hash_name", "listing_id",
    "price_usd", "csfloat_predicted_price_usd",
    "float_value", "wear_name",
    "paint_seed", "paint_index", "phase",
    "is_stattrak", "is_souvenir",
    "rarity", "quality",
    "sticker_count", "sticker_total_value_usd", "sticker_names", "stickers_raw",
]


def fetch_csfloat_listings(skin_name, max_pages=3):
    """Pull up to max_pages * 50 buy_now listings for one skin from CSFloat."""
    all_listings = []

    for page in range(max_pages):
        params = {
            "market_hash_name": skin_name,
            "limit": 50,
            "sort_by": "lowest_price",
            "type": "buy_now",
            "page": page,
        }
        response = requests.get(
            "https://csfloat.com/api/v1/listings",
            params=params,
            headers={"Authorization": CSFLOAT_API_KEY}
        )

        if response.status_code == 429:
            print(f"  Rate limited — waiting 10s...")
            time.sleep(10)
            response = requests.get(
                "https://csfloat.com/api/v1/listings",
                params=params,
                headers={"Authorization": CSFLOAT_API_KEY}
            )

        if response.status_code != 200:
            print(f"  HTTP {response.status_code} on page {page}, stopping.")
            break

        page_listings = response.json().get("data", [])
        all_listings.extend(page_listings)

        if len(page_listings) < 50:
            break  # fewer than a full page means no more results

        time.sleep(1)  # ~1 req/sec

    return all_listings


def parse_listing(listing, skin_name, timestamp):
    """Flatten one CSFloat listing object into a CSV-ready dict."""
    item = listing.get("item", {}) or {}
    stickers = item.get("stickers", []) or []

    # listing["reference"] is a top-level object with base_price, float_factor, predicted_price.
    # Stickers have their own nested ["reference"]["price"]. These are different namespaces.
    listing_ref = listing.get("reference", {}) or {}

    # Each sticker's price lives at sticker["reference"]["price"] in cents (not "market_value").
    sticker_total_cents = sum(
        (s.get("reference", {}) or {}).get("price", 0) or 0
        for s in stickers
    )

    predicted_raw = listing_ref.get("predicted_price")

    return {
        "timestamp": timestamp,
        "market_hash_name": skin_name,
        "listing_id": listing.get("id", ""),
        "price_usd": round(listing.get("price", 0) / 100, 2),
        "csfloat_predicted_price_usd": round(predicted_raw / 100, 2) if predicted_raw else "",
        "float_value": item.get("float_value", ""),
        "wear_name": item.get("wear_name", ""),
        "paint_seed": item.get("paint_seed", ""),
        "paint_index": item.get("paint_index", ""),
        "phase": item.get("phase", ""),           # Ruby / Sapphire / Phase 1-4 / etc. — null for non-Doppler
        "is_stattrak": item.get("is_stattrak", False),
        "is_souvenir": item.get("is_souvenir", False),
        "rarity": item.get("rarity_name", ""),    # rarity_name = "Classified" (rarity is a raw int)
        "quality": item.get("quality", ""),
        "sticker_count": len(stickers),
        "sticker_total_value_usd": round(sticker_total_cents / 100, 2),
        "sticker_names": json.dumps([s.get("name", "") for s in stickers]),
        "stickers_raw": json.dumps(stickers),     # full blob; parse later if needed
    }


def fetch_all_listings():
    """Fetch per-listing CSFloat data for LISTING_SKINS and append to listings.csv."""
    file_exists = os.path.exists(LISTINGS_FILE)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_saved = 0

    with open(LISTINGS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LISTINGS_HEADERS)
        if not file_exists:
            writer.writeheader()

        for skin in LISTING_SKINS:
            max_pages = 4 if skin in LISTING_SKINS_DEEP else 3
            print(f"Fetching listings: {skin} (max {max_pages * 50} listings)")
            listings = fetch_csfloat_listings(skin, max_pages=max_pages)

            if not listings:
                print("  No listings found.")
                continue

            for listing in listings:
                writer.writerow(parse_listing(listing, skin, timestamp))

            print(f"  {len(listings)} listings saved.")
            total_saved += len(listings)
            time.sleep(1)

    print(f"\nDone. Total listings saved: {total_saved}")


# --- RUN ---
# get_current_prices()          # old per-platform snapshot
# take_snapshot()               # aggregate snapshot (steam/skinport/csfloat min+avg) — run daily if still needed

fetch_all_listings()          # per-listing CSFloat data for hedonic model — run this

# for skin in skins:            # pull full steam history for all skins
#     data = get_price_history(skin)
#     if "prices" in data:
#         save_history(skin, data["prices"])
#     else:
#         print(f"{skin} → failed, got: {data}")
#     time.sleep(5)

# skin = "AWP | Neo-Noir (Field-Tested)"   # pull history for single skin
# data = get_price_history(skin)
# if "prices" in data:
#     save_history(skin, data["prices"])
# else:
#     print(f"failed, got: {data}")