"""Full-featured price prediction model.

Where analysis.py fits one interpretable feature (float_value) per skin and
reports how much variance it explains, this file fits ONE model across all
skins using every feature we collect (float, pattern/seed, phase, StatTrak,
stickers, rarity...) and asks a different question: how close can we get to
predicting a listing's actual price_usd?

We use gradient-boosted trees (HistGradientBoostingRegressor), not a linear
model, because:
  - it handles missing values natively (phase is null for ~78% of rows —
    non-Doppler skins don't have one)
  - it handles categorical features (market_hash_name, phase, rarity...)
    without manual one-hot encoding
  - it can learn interactions on its own (e.g. "paint_seed only matters for
    Case Hardened / Fade / Doppler skins") instead of us hand-building
    is_blue_gem-style flags for every pattern skin

We train on log(price_usd) instead of raw price_usd because prices span
$27 to $50,000 across skins — an untransformed model would spend all its
effort on the few expensive knives and barely fit the cheap skins at all.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from analysis import load_listings, LISTINGS_FILE

PREDICTIONS_FILE = "data/processed/model_predictions.csv"

NUMERIC_FEATURES = ["float_value", "paint_seed", "paint_index", "sticker_count", "sticker_total_value_usd"]
CATEGORICAL_FEATURES = ["market_hash_name", "wear_name", "phase", "rarity", "quality", "is_stattrak", "is_souvenir"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def build_features(df):
    """Return (X, y, df) with categorical dtypes set so HistGradientBoostingRegressor
    can use categorical_features="from_dtype" instead of manual one-hot encoding."""
    df = df.dropna(subset=["price_usd"]).copy()
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].astype("category")
    X = df[FEATURES]
    y = np.log(df["price_usd"])
    return X, y, df


def train_model(X_train, y_train):
    model = HistGradientBoostingRegressor(
        categorical_features="from_dtype",
        max_iter=300,
        learning_rate=0.05,
        random_state=42,
    )
    model.fit(X_train, y_train)
    return model


def evaluate(model, X_test, y_test, df_test):
    """Dollar-scale metrics (back-transformed from log), overall and per-skin,
    plus a head-to-head against CSFloat's own predicted price on the same rows."""
    log_pred = model.predict(X_test)
    pred_usd = np.exp(log_pred)
    actual_usd = np.exp(y_test.values)

    overall = {
        "n": len(actual_usd),
        "r2_log": r2_score(y_test, log_pred),
        "mae_usd": mean_absolute_error(actual_usd, pred_usd),
        "mape": float(np.mean(np.abs(pred_usd - actual_usd) / actual_usd)),
        "csfloat_mae_usd": mean_absolute_error(actual_usd, df_test["csfloat_predicted_price_usd"]),
        "csfloat_mape": float(np.mean(
            np.abs(df_test["csfloat_predicted_price_usd"] - actual_usd) / actual_usd
        )),
    }

    per_skin = df_test.assign(predicted_price_usd=pred_usd).groupby("market_hash_name", observed=True).apply(
        lambda g: pd.Series({
            "n": len(g),
            "mae_usd": mean_absolute_error(g["price_usd"], g["predicted_price_usd"]),
            "mape": float(np.mean(np.abs(g["predicted_price_usd"] - g["price_usd"]) / g["price_usd"])),
            "csfloat_mape": float(np.mean(
                np.abs(g["csfloat_predicted_price_usd"] - g["price_usd"]) / g["price_usd"]
            )),
        }),
        include_groups=False,
    ).sort_values("mape")

    return overall, per_skin, pred_usd


def feature_importance(model, X_test, y_test, n_repeats=10):
    """Permutation importance: how much log-scale R^2 drops when each feature
    is shuffled. HistGradientBoostingRegressor has no built-in feature_importances_."""
    result = permutation_importance(
        model, X_test, y_test, n_repeats=n_repeats, random_state=42, scoring="r2"
    )
    return pd.Series(result.importances_mean, index=X_test.columns).sort_values(ascending=False)


def run():
    df = load_listings(LISTINGS_FILE)
    X, y, df = build_features(df)

    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y, df, test_size=0.2, random_state=42, stratify=df["market_hash_name"]
    )

    model = train_model(X_train, y_train)
    overall, per_skin, pred_usd = evaluate(model, X_test, y_test, df_test)
    importances = feature_importance(model, X_test, y_test)

    pd.set_option("display.width", 140)
    print(f"\nOverall (n={overall['n']} test listings):")
    print(f"  log-scale R^2:        {overall['r2_log']:.3f}")
    print(f"  MAE:                  ${overall['mae_usd']:.2f}   (CSFloat: ${overall['csfloat_mae_usd']:.2f})")
    print(f"  MAPE:                 {overall['mape']:.1%}   (CSFloat: {overall['csfloat_mape']:.1%})")

    print("\nPer-skin MAPE, ours vs CSFloat's predicted price:")
    print(per_skin.to_string())

    print("\nPermutation importance (log R^2 drop when feature is shuffled):")
    print(importances.to_string())

    out = df_test[["market_hash_name", "listing_id", "price_usd", "csfloat_predicted_price_usd"]].copy()
    out["predicted_price_usd"] = pred_usd
    out["residual_usd"] = out["price_usd"] - out["predicted_price_usd"]
    out["csfloat_residual_usd"] = out["price_usd"] - out["csfloat_predicted_price_usd"]
    out.to_csv(PREDICTIONS_FILE, index=False)
    print(f"\nSaved {len(out)} test-set predictions to {PREDICTIONS_FILE}")

    return overall, per_skin, importances


if __name__ == "__main__":
    run()
