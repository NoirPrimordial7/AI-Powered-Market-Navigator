# Data provenance

The repository's six daily OHLCV CSVs are **demonstration/evaluation histories collected for this release**, not the missing original training dataset. Symbols: AAPL, MSFT, NVDA, SPY, RELIANCE.NS and TCS.NS. Collection times and exact date ranges are recorded in [`data/provenance.json`](../data/provenance.json); file hashes used for evaluation are recorded in [`evaluation/metrics.json`](../evaluation/metrics.json).

Source: Yahoo Finance through `yfinance` 0.2.66. US histories cover 3 October 2025 through 2 October 2026; Indian histories cover 3 October 2025 through 1 October 2026. Quote currencies are USD and INR respectively. Market closures mean the row counts/date intersections differ. Prices reflect the provider/yfinance adjustment conventions at collection; they are not point-in-time vintage records. Future corrections, corporate-action adjustments and vendor revisions can change a fresh download.

Columns: Date, Open, High, Low, Close and Volume. Technical indicators are computed by the app, not supplied as model training labels. The evaluation uses 63 final targets per symbol; it fits scaling using only data available before each target. Full target-by-target results are in [`evaluation/predictions.csv`](../evaluation/predictions.csv).

## Usage and ownership

Financial provider data is separate from the project's code/model copyright. This project grants no independent redistribution or commercial data license. `yfinance` is an unofficial research/educational client, is not endorsed by Yahoo, and its [official README](https://github.com/ranaroussi/yfinance) directs users to Yahoo's terms and notes personal-use restrictions. Review the relevant provider terms before extending this demonstration into public data redistribution, commercial use or a production service.

News is limited to publisher feed headlines, publication dates, short deterministic event context and destination links. Complete news articles are not scraped or bundled. Publisher copyright remains with CNBC, the Federal Reserve, Yahoo Finance and the underlying article publishers. Headlines are fetched at runtime and are not a model input or a historical training dataset.

Uploaded CSVs are held in the visitor's Streamlit session and are not written to a shared upload directory or committed. Internal watchlist URLs contain public tickers only, without holdings or account information. No trading account connection exists.

## Refresh and reproduction

`python prepare_data.py` explicitly downloads new example histories and rewrites their provenance. It never runs automatically for website visitors. Refreshing changes the evaluation inputs; rerun `python evaluate.py` and publish the new dataset hashes/results together. Do not compare reports generated on different inputs as if they were the same experiment.

For a new training run, supply an OHLCV CSV with an appropriate usage license and sufficient history. The training recipe writes its input hash, chronological ranges and sample counts to `run.json`. Keep data provenance and original provider terms with every separately shared training dataset.

## Verified release observations

[The source audit](../evaluation/data-audit.json) checks 251 rows per symbol (1,506 total). All rows had ordered, unique, non-future dates; finite positive prices; valid high/low bounds; and nonnegative integer volume. A fresh Yahoo download for the same ranges matched every date and volume exactly, with no missing or extra dates. Currencies were USD for US symbols and INR for Indian symbols.

Adjusted OHLC cells had small numerical differences, at most 0.000256 quote units. The report records both strict tolerances (relative 1e-7, absolute 1e-5) and differences exceeding 0.01 units; none exceeded 0.01. Some strict checks failed and are retained explicitly. This does not prove byte-exact prices, point-in-time adjustment validity or independent exchange correctness.

Reproduce manually with `python audit_data.py`. This updates only the audit report, never the source CSVs; provider revisions can change later comparisons.
