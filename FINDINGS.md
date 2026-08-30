# Findings Log — Hedonic Pricing Model

Running, dated record of what we've actually learned from the data. Order = order
discovered. This is the raw material for the eventual README writeup — keep entries
short and factual, one finding per entry.

---

## 2026-07-14 — Float explains almost nothing for AK-47 Redline (FT)

Regression: `price_usd ~ float_value`, AK-47 | Redline (Field-Tested) only, n=505
(deduped on `listing_id`).

- Float range in sample: 0.24–0.37
- Price range: $27.50–$34.76
- Slope: -9.85, **R² = 0.030**, corr = -0.17

**Takeaway:** within one wear tier, float barely moves Redline's price. The FT wear
band already compresses float into a narrow range, and Redline has no pattern/seed
effect, so there's not much left for float alone to explain. A single-feature float
model is not going to be a good fair-value model for this skin.

---

## 2026-07-14 — Driver Gloves | King Snake (FT) shows a strong float effect

Same regression, ★ Driver Gloves | King Snake (Field-Tested), n=400.

- Float range: 0.16–0.38 (wider than Redline's FT band)
- Price range: $144.07–$320.00
- Slope: -559.16, **R² = 0.525**, corr = -0.72

**Takeaway:** this is the sharpest contrast we have so far. Same single-feature model,
same wear tier, but float explains ~17x more price variance than it did for Redline.
Working hypothesis: gloves have no competing pattern/seed effect and no sticker
economy, so float is closer to the *only* thing differentiating two listings — makes
the float→price relationship much cleaner. Redline's weak result isn't a modeling
failure, it's telling us float genuinely isn't the dominant driver for that skin.

---

## 2026-07-14 — Driver Gloves | Crimson Weave and Convoy (FT) are inconclusive — not enough data

Same regression attempted on two more finishes:

- Crimson Weave (FT): n=21, R² = 0.006, corr = -0.07
- Convoy (FT): n=8, R² = 0.002, corr = -0.05

**Takeaway:** these R² values are noise, not signal — CSFloat only has 21 and 8
Field-Tested buy_now listings for these finishes total. Not usable until more listings
accumulate (or unless we pull other wear tiers too). Replaced with three more liquid
finishes (Overtake, Racing Green, Snow Leopard — each had a full 50-listing first page
on CSFloat, so likely 100+ each) to get a proper 4-finish comparison. Fetch was in
progress when this log was started; results to be added once it completes.

---

## 2026-07-14 — Data coverage check across all skins currently in `listings.csv`

Deduped on `listing_id` (raw file has repeat rows from re-running fetches on the same
listings). Current unique listing counts by skin:

| Skin | n | Notes |
|---|---:|---|
| ★ Karambit \| Doppler (FN) | 527 | pattern/phase skin — float-only regression not meaningful yet, see below |
| ★ M9 Bayonet \| Doppler (FN) | 521 | same |
| AK-47 \| Redline (FT) | 505 | analyzed above |
| AK-47 \| Case Hardened (FT) | 482 | pattern skin |
| ★ Driver Gloves \| King Snake (FT) | 400 | analyzed above |
| Glock-18 \| Gamma Doppler (FN) | 272 | pattern/phase skin |
| AK-47 \| Asiimov (FT) | 257 | not yet analyzed |
| AWP \| Asiimov (FT) | 249 | not yet analyzed |
| AWP \| Neo-Noir (FT) | 241 | not yet analyzed |
| Desert Eagle \| Blaze (FN) | 236 | not yet analyzed |
| M4A1-S \| Hyper Beast (FT) | 230 | not yet analyzed |
| ★ Karambit \| Fade (FN) | 229 | pattern skin |
| Desert Eagle \| Printstream (FN) | 209 | not yet analyzed |
| ★ Karambit \| Case Hardened (FT) | 199 | pattern skin |
| M4A1-S \| Printstream (FN) | 193 | not yet analyzed |
| ★ M9 Bayonet \| Fade (FN) | 186 | pattern skin |
| ★ Flip Knife \| Fade (FN) | 157 | pattern skin |
| USP-S \| Kill Confirmed (FN) | 125 | not yet analyzed |
| M4A1-S \| Hyper Beast (FN) | 109 | not yet analyzed |
| M4A4 \| Howl (FT) | 86 | not yet analyzed |
| ★ Driver Gloves \| Crimson Weave (FT) | 21 | too thin, see above |
| ★ Driver Gloves \| Convoy (FT) | 8 | too thin, see above |

**Answer to "do we have enough data yet":**

- **Non-pattern skins (Redline, Asiimov, Neo-Noir, Blaze, Printstream, Hyper Beast,
  Kill Confirmed, Howl, gloves besides the two thin finishes):** yes, n=86–505 each is
  enough to run the same single-feature float→price regression we just ran twice, and
  get a real (not noise) R². These are ready to batch-process right now.
- **Pattern/phase skins (Case Hardened, Fade, Doppler variants):** n is fine (186–527),
  but a raw float-only regression on these will be misleading — seed/phase is doing
  most of the price work and isn't in the model yet. Need the seed→feature engineering
  (blue-gem %, fade %, phase dummy) from the project plan before these numbers mean
  anything. Don't report float R² for these yet.
- **Crimson Weave / Convoy gloves:** not enough data, addressed above.

---

## 2026-07-14 — Batch float regression across all "ready" non-pattern skins, snapshot-normalized

Problem noticed: `listings.csv` spans 2026-05-29 to 2026-07-14 across 9 separate fetch
runs, so pooling raw prices across all of them mixes different market regimes (overall
price drift) into what's supposed to be a single point-in-time cross-section. Fixed by
adding `relative_price = price_usd / (median price for that skin at that fetch
timestamp)` and regressing on that instead of raw price — cancels day-level drift,
isolates the within-snapshot float premium. Implemented in `src/analysis.py`
(`add_relative_price`, `float_regression`, `run_batch`).

Results, raw-pooled R² vs. snapshot-normalized R², sorted by normalized R²:

| Skin | n | # snapshots | R² raw pooled | R² normalized | corr (normalized) |
|---|---:|---:|---:|---:|---:|
| ★ Driver Gloves \| King Snake (FT) | 400 | 1 | 0.525 | 0.525 | -0.72 |
| M4A1-S \| Printstream (FN) | 193 | 5 | 0.234 | 0.221 | -0.47 |
| AWP \| Asiimov (FT) | 249 | 7 | 0.111 | 0.166 | -0.41 |
| AK-47 \| Asiimov (FT) | 257 | 5 | 0.111 | 0.145 | -0.38 |
| Desert Eagle \| Printstream (FN) | 209 | 5 | 0.073 | 0.081 | -0.28 |
| Desert Eagle \| Blaze (FN) | 236 | 5 | 0.071 | 0.048 | -0.22 |
| M4A1-S \| Hyper Beast (FN) | 109 | 5 | 0.056 | 0.042 | -0.21 |
| AK-47 \| Redline (FT) | 505 | 6 | 0.028 | 0.041 | -0.20 |
| AWP \| Neo-Noir (FT) | 241 | 5 | 0.014 | 0.034 | -0.18 |
| USP-S \| Kill Confirmed (FN) | 125 | 5 | 0.038 | 0.025 | -0.16 |
| M4A1-S \| Hyper Beast (FT) | 230 | 5 | 0.001 | 0.001 | -0.04 |
| M4A4 \| Howl (FT) | 86 | 5 | 0.000 | 0.000 | -0.01 |

**Takeaways:**

- King Snake gloves remain the clear outlier — float alone explains over half the price
  variance. Nothing else comes close.
- Second tier (M4A1-S Printstream, AK/AWP Asiimov) shows a real but moderate float
  effect (R²≈0.11–0.23) — worth keeping in mind as a middle category between "float
  barely matters" and "float is almost everything."
- Bottom group (Redline, Neo-Noir, Kill Confirmed, Hyper Beast FT, Howl) all sit under
  R²=0.04 — float is close to irrelevant for these within one wear tier.
- Snapshot normalization changed individual R² values by only a few points either way
  for this dataset (e.g. Redline 0.028→0.041, Asiimov AWP 0.111→0.166) — real but not
  dramatic yet, since most skins so far have only 5-7 snapshots over ~7 weeks. Keeping
  the normalization anyway: it's the methodologically correct approach and the effect
  will matter more as more time passes and more snapshots accumulate. King Snake has
  only 1 snapshot so far, so normalization is a no-op for it until it's re-fetched on a
  different day.

---

## 2026-08-30 — Full-feature gradient boosting model matches CSFloat's own predicted price overall, but loses badly on pattern skins with thin data

New model (`src/model.py`), separate from the per-skin float regressions above. One
`HistGradientBoostingRegressor` trained on log(price_usd) across all 25 skins at once,
using every feature we collect: float_value, paint_seed, paint_index, phase,
is_stattrak, is_souvenir, rarity, quality, sticker_count, sticker_total_value_usd,
market_hash_name. 80/20 train/test split (stratified by skin), n=7,761 listings total,
1,553 in the test set.

**Headline result — beats CSFloat's black-box predictor on average:**

| | MAE | MAPE |
|---|---:|---:|
| Our model | $139.69 | 13.0% |
| CSFloat's `csfloat_predicted_price_usd` | $148.23 | 13.6% |
| log-scale R² | 0.976 | |

**But this hides a big split by skin type.** Per-skin MAPE (see `run()` output / analysis
below):
- Non-pattern skins (Redline, Asiimov, Neo-Noir, Hyper Beast, Printstream, Blaze, Gamma
  Doppler, gloves): our model matches or beats CSFloat, often by a lot (Redline 4.7% vs
  8.3%; Blaze 7.4% vs 11.6%; Gamma Doppler 8.8% vs 10.7%).
- Pattern/seed skins are where it breaks: **★ Karambit | Case Hardened is 65.9% MAPE for
  our model vs 37.0% for CSFloat** — almost 2x worse. AK-47 Case Hardened, Karambit Fade,
  and the two illiquid glove finishes (Crimson Weave n=4, Convoy n=2 in test) are the
  other clear losses.

**Why:** permutation importance shows `market_hash_name` completely dominates (0.81 drop
in log R² when shuffled), `float_value` is a distant second (0.016), and `paint_seed` /
`paint_index` barely register (0.001–0.002) despite being the whole story for Case
Hardened/Fade/Doppler pricing. Working theory: blue-gem-tier Case Hardened seeds are a
short, non-contiguous list of "magic numbers" (specific seed IDs worth 10–50x a normal
seed) — a raw integer paint_seed feature gives a tree nothing smooth to split on, and with
only ~200 total listings for Karambit Case Hardened (43 in test), there isn't enough data
per seed value for the model to memorize which specific seeds are the valuable ones.
This is exactly the seed-based feature engineering the original project plan called for
(is_blue_gem flags etc.) and confirms it's necessary, not optional, before pattern skins
can be trusted from either model.

**Takeaway:** the model is legitimately good — and already the stronger of the two on
most skins — for skins where float/attributes are the price driver. It should not be
trusted yet for pattern-dependent skins. Predictions saved to
`data/processed/model_predictions.csv` (test set only, with residuals vs. both our model
and CSFloat's).

---

## Open items carried forward (not findings yet, just tracked)

- ~~Re-run the float regression across all "ready" non-pattern skins~~ — done above.
- ~~Benchmark our model's error against CSFloat's own `csfloat_predicted_price_usd`
  column~~ — done above, we beat it 13.0% vs 13.6% MAPE overall.
- **Build seed-based features for pattern skins** (is_blue_gem for Case Hardened, fade %
  for Fade, phase-tier dummies for Doppler) — now confirmed necessary: raw paint_seed is
  nearly useless to the model (importance 0.001) despite driving most of the price
  variance for these skins. This is the clear next step.
- Consider a per-skin-family model (or at least separate pattern-skin handling) instead of
  one global model, since pattern skins need fundamentally different features than
  float-driven skins.
- `README.md` is still an empty placeholder — write it once the seed-feature pass is in,
  using this log (float findings + CSFloat benchmark + seed-feature results) as source
  material.
