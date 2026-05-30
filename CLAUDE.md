# CS2 Skins Quant Project — Context for Claude Code

## What this project is
A quantitative research project on the Counter-Strike 2 (CS2) skins market, built in
Python. The goal is to look impressive for quant trading firms and FAANG recruiters, be
buildable solo over one summer, and teach me real quant/data-science skills along the way.

I am a student. Explain things clearly when relevant, but I can read and run Python.

## Current state
- Project folder: `cs2-quant`
- Stack: Python 3.9, pandas, requests, jupyter, (sklearn coming for modeling)
- Virtual environment lives in `venv/`
- `src/fetch.py` already works and collects data
- `data/raw/snapshots.csv` has ~1 week of daily AGGREGATE price snapshots
  (steam_lowest, steam_median, steam_volume, skinport_avg_24h, skinport_median_24h,
  skinport_volume_24h, skinport_avg_30d, csfloat_lowest, csfloat_avg_top10) for ~60 skins.
- I run fetch.py manually 1-2x/day (no automation set up; that's fine for now).

## IMPORTANT: the pivot
The original idea was cross-platform ARBITRAGE (buy cheap on one venue, sell high on
another). I've since learned this is NOT feasible for a solo student because of:
- Steam's 7-day trade hold on received items (2018 rule)
- Steam's "Trade Protection" 7-day reversal window (added July 2025)
- The 1-week hold on anything bought from the Steam Community Market
- 15% Steam fees, $1,800 listing cap / $2,000 wallet cap
- Steam wallet funds CANNOT be cashed out to real money
The price gaps between venues are the market pricing in this friction, not free money.

## THE ACTUAL PROJECT (Project 2): Hedonic float/pattern pricing model
Build a "fair value" model for individual skin listings based on their attributes, then
flag listings priced below model value. This is structurally like equity factor/fair-value
modeling — the most "quant" version of this project.

### Reframe (important):
CSFloat already shows a predicted price per listing. So the project is NOT "invent a price
predictor no one has." It's: **build my own interpretable fair-value model, BENCHMARK it
against CSFloat's production predictor, and decompose what actually drives skin prices
(float vs pattern vs stickers vs StatTrak).** That comparison + interpretability is the
strong, defensible quant story.

### Data needed (DIFFERENT from what I have):
The snapshots.csv only has aggregate min/avg prices — NOT enough.
For Project 2 I need PER-LISTING data: every individual listing as its own row with its
own float, pattern seed, price, etc. This is a cross-section (many different items of the
same skin at one moment), which is what teaches the price-vs-float relationship.

Need to fetch, per listing:
- market_hash_name
- float_value
- paint_seed
- paint_index
- price (CSFloat returns cents — divide by 100)
- is_stattrak
- stickers (and ideally summed sticker value)
- type (filter to buy_now only; auctions pollute prices)

Save to something like `data/raw/listings.csv` with a timestamp column.
Run over time to accumulate more items (CSFloat caps 50 listings/request) and to enable
Project 4 later.

### Modeling approach:
1. Start with ONE skin (e.g. AK-47 Redline FT, or a pattern skin like Case Hardened).
2. Plot price vs float — expect downward slope (lower float = higher price).
3. Fit regression: start with `price ~ float`, then add features.
   sklearn LinearRegression, then try more flexible models.
4. Feature engineering:
   - float_value (continuous)
   - is_stattrak (bool)
   - sticker_value (continuous)
   - pattern flags: seed is CATEGORICAL not numeric. Convert known special seeds to
     boolean flags (e.g. is_blue_gem for Case Hardened seed 661). Ignore seed for
     non-pattern skins.
5. Normalize prices by the skin's daily median to model the RELATIVE float premium
   (more stable over time than absolute price). The price-vs-float SHAPE is more stable
   than the LEVEL.
6. Compute residuals: actual_price - predicted_price. Big negative residual = potentially
   underpriced listing. That residual column is the payoff.
7. Validate: is the float effect statistically significant? R^2? Are "underpriced" flags
   consistent or noise? Compare my predictions vs CSFloat's predicted price.

## Project 4 (LATER, bolts onto Project 2): fee/hold-aware paper-trading backtester
A simulator that answers "if I'd actually acted on my model's underpriced flags, would I
make money AFTER real friction?" Walks historical data day by day; when the model flags a
buy, simulate buying, wait the mandatory 7-day hold, simulate selling at the later price,
subtract fees. Report PnL, Sharpe, max drawdown, hold-time distribution. Cannot exist
without Project 2's signal. This is the "execution/strategy" quant angle.

## APIs (verified)
### CSFloat — PRIMARY source for Project 2
- Base: https://csfloat.com/api/v1
- Auth: header `Authorization: <API-KEY>` (I have a key)
- `GET /listings` params: market_hash_name, limit (max 50), sort_by (lowest_price etc),
  type (buy_now/auction), min_float, max_float, paint_seed, paint_index, category, min_price, max_price
- Response: listings are nested under the `data` key (data.get("data", [])).
  Each listing has item.float_value, item.paint_seed, item.paint_index,
  item.is_stattrak, item.stickers, and top-level price (in CENTS).
- Prices are in cents — divide by 100.
- Filter type=buy_now (auctions return live bid prices that pollute data).
- No documented numeric rate limit (only 429 code). Use ~1 req/sec, back off on 429.

### Skinport — aggregate sales stats (good for the spread side / context)
- Docs: https://docs.skinport.com/category/introduction
- `GET https://api.skinport.com/v1/sales/history` — NO auth.
- Params: market_hash_name (comma-delimited), app_id (default 730), currency (default EUR, supports USD)
- REQUIRES header `Accept-Encoding: br` (Brotli). Need `brotli` pip package.
- Returns min/max/avg/median/volume for last 24h, 7d, 30d, 90d (rolling windows, NOT daily history).
- Rate limit: 8 requests / 5 min. Cached 5 min.

### Steam Community Market — long historical daily price data
- priceoverview: https://steamcommunity.com/market/priceoverview/?appid=730&currency=1&market_hash_name=...
  (lowest_price, median_price, volume). currency=1 is USD.
- pricehistory: https://steamcommunity.com/market/pricehistory/ — requires being LOGGED IN;
  send `steamLoginSecure` cookie. Returns daily [date, price, volume] going back years.
- No official API; these are undocumented endpoints. Rate limited (~1 req/sec, can temp-IP-ban).
- Steam cookie expires every few weeks; refresh from DevTools > Application > Cookies.
- ToS note: reading public price data is OK; AUTOMATING TRADES/market actions violates ToS.
  Keep everything to reads + paper trading. Never share the Steam Web API key.

## Skin-name gotchas (learned the hard way)
- Knife/glove names need a real unicode star: `★ M9 Bayonet` (not `*`).
- Vanilla knives have NO wear tier in the name: `★ Karambit`, `★ M9 Bayonet`, `★ Skeleton Knife`,
  `★ Gut Knife`, `★ Flip Knife` (NOT `... (Factory New)`).
- Cases have no wear tier: `Fracture Case`, `Horizon Case`, etc.
- M4A4 Howl is contraband — N/A on Steam (over the price cap / not normally listed); fine on CSFloat/Skinport.
- Some skins have no FN/MW because their float floor is too high.
- Steam sometimes returns partial data — use .get(...) with defaults, never hard index.
- Lock the skins list and stop changing it, or the time series gets gaps.

## Folder structure
```
cs2-quant/
  data/raw/        # raw API output (snapshots.csv, listings.csv, *_history.csv)
  data/processed/  # cleaned data for analysis
  notebooks/       # jupyter analysis
  src/
    fetch.py       # data collection (works)
    store.py
    analysis.py
  venv/
  README.md
  requirements.txt
  CLAUDE.md        # this file
```

## Conventions / preferences
- Keep code readable and commented; I'm still learning.
- Use .get() defensively on all API responses.
- Save raw API data untouched in data/raw/; do cleaning into data/processed/.
- Use a virtualenv; pip install with the venv active (python3 on Mac, not python).
- The big README writeup matters as much as the code for recruiting — keep notes for it.

## Immediate next step
Write a new function (or new script) that pulls every CSFloat buy_now listing for each
skin in my list and saves per-listing float_value, paint_seed, paint_index, price (÷100),
is_stattrak, and sticker info to data/raw/listings.csv with a timestamp. This is the
training data for the hedonic pricing model.
