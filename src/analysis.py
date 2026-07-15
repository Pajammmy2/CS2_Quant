import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

LISTINGS_FILE = "data/raw/listings.csv"

# Non-pattern skins only — pattern/phase skins (Case Hardened, Fade, Doppler) need
# seed-based features before a float-only regression means anything (see FINDINGS.md).
# Driver Gloves | Crimson Weave / Convoy excluded — too few FT listings (21 / 8) to be
# anything but noise.
READY_SKINS = [
    "AK-47 | Redline (Field-Tested)",
    "AK-47 | Asiimov (Field-Tested)",
    "AWP | Asiimov (Field-Tested)",
    "AWP | Neo-Noir (Field-Tested)",
    "Desert Eagle | Blaze (Factory New)",
    "Desert Eagle | Printstream (Factory New)",
    "M4A1-S | Hyper Beast (Field-Tested)",
    "M4A1-S | Hyper Beast (Factory New)",
    "M4A1-S | Printstream (Factory New)",
    "USP-S | Kill Confirmed (Factory New)",
    "M4A4 | Howl (Field-Tested)",
    "★ Driver Gloves | King Snake (Field-Tested)",
]


def load_listings(path=LISTINGS_FILE):
    """Load listings.csv, deduped on listing_id (repeat fetches re-save the same
    still-live listing under a new timestamp row)."""
    df = pd.read_csv(path)
    return df.drop_duplicates(subset="listing_id", keep="last")


def add_relative_price(df):
    """relative_price = price / (median price for that skin at that fetch timestamp).

    Pooling raw prices across fetches taken weeks apart mixes different market
    regimes (overall price drift) into what should be a same-moment cross-section.
    Dividing by the same-snapshot median cancels day-level drift so the float
    coefficient reflects the within-snapshot float premium, not market movement.
    """
    df = df.copy()
    snapshot_median = df.groupby(["market_hash_name", "timestamp"])["price_usd"].transform("median")
    df["relative_price"] = df["price_usd"] / snapshot_median
    return df


def float_regression(df, skin_name, target_col):
    sub = df[df["market_hash_name"] == skin_name].dropna(subset=["float_value", target_col])
    n = len(sub)
    if n < 5:
        return None
    X = sub[["float_value"]].values
    y = sub[target_col].values
    reg = LinearRegression().fit(X, y)
    pred = reg.predict(X)
    r2 = r2_score(y, pred)
    corr = sub["float_value"].corr(sub[target_col])
    return {
        "n": n,
        "n_timestamps": sub["timestamp"].nunique(),
        "slope": reg.coef_[0],
        "r2": r2,
        "corr": corr,
    }


def run_batch(skins=READY_SKINS):
    """Compare raw-pooled vs. snapshot-normalized float regression for each skin."""
    df = add_relative_price(load_listings())
    rows = []
    for skin in skins:
        raw = float_regression(df, skin, "price_usd")
        norm = float_regression(df, skin, "relative_price")
        if raw is None or norm is None:
            continue
        rows.append({
            "skin": skin,
            "n": raw["n"],
            "n_timestamps": raw["n_timestamps"],
            "r2_raw_pooled": round(raw["r2"], 4),
            "r2_normalized": round(norm["r2"], 4),
            "corr_normalized": round(norm["corr"], 4),
        })
    return pd.DataFrame(rows).sort_values("r2_normalized", ascending=False)


if __name__ == "__main__":
    result = run_batch()
    pd.set_option("display.width", 140)
    print(result.to_string(index=False))
