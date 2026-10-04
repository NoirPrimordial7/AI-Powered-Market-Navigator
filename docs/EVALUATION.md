# Evaluation of the current app pipeline

**378 next-session predictions; original training overlap is unknown. This is a pipeline diagnostic, not verified independent holdout performance.**

The last 63 targets of each saved symbol are predicted chronologically. For target row i, features and MinMax scaling use only rows before i. There is no future row in the input or fitted scaler. Causal indicators can be computed on the full series because their value at a date depends only on earlier observations. Original pretraining data/scaler remain unknown, and adjusted vendor histories may include later corporate-action revisions.

The baseline predicts the next closing price equals the last observed closing price (persistence). Price errors are reported separately per symbol in its quote currency. Macro MAPE is the unweighted mean of six per-symbol MAPEs.

| Symbol | Targets | Model MAE | Model RMSE | Model MAPE | Baseline MAPE | Model R² | Direction correct |
|---|---:|---:|---:|---:|---:|---:|---:|
| AAPL (USD) | 63 | 70.37 | 71.30 | 21.74% | 1.20% | -37.340 | 46.03% |
| MSFT (USD) | 63 | 100.53 | 111.58 | 20.57% | 1.46% | -4.271 | 42.86% |
| NVDA (USD) | 63 | 45.40 | 46.52 | 20.87% | 1.87% | -19.387 | 46.03% |
| RELIANCE.NS (INR) | 63 | 23.70 | 27.83 | 1.85% | 0.98% | 0.483 | 59.68% |
| SPY (USD) | 63 | 118.82 | 119.33 | 15.64% | 0.55% | -105.140 | 53.97% |
| TCS.NS (INR) | 63 | 200.84 | 234.50 | 8.65% | 1.43% | -2.672 | 61.29% |

**Macro MAPE: model 14.89%; persistence 1.25%.** Every evaluated symbol underperforms persistence on MAPE. This diagnostic does not justify claims of validated predictive skill.

![Per-symbol percentage error](../assets/evaluation.svg)

MAE = mean absolute price error; RMSE = square root of mean squared price error; MAPE = mean absolute percentage error relative to actual price; R² = 1 − squared-error sum / actual-price variance sum. Negative R² means worse squared error than using the sample mean as a descriptive reference, not a forward-available trading baseline.

Directional accuracy compares the sign of forecast minus origin close with actual minus origin close. Zero actual moves are excluded. A flat/persistence prediction abstains; it counts as incorrect on a nonzero actual move, so its strict direction score is zero. Do not use that convention as evidence of useful skill without a directional baseline. There are 63 direction targets for each US symbol and 62 for each Indian symbol. No confidence intervals or significance claims are made; daily errors are correlated.

The checked target ranges are in [metrics.json](../evaluation/metrics.json); the complete 378 origin/target rows, prices and forecasts are in [predictions.csv](../evaluation/predictions.csv). Every input file and the model have recorded SHA-256 hashes.

```sh
python evaluate.py
python -m unittest discover -s tests -v
```

Run from the repository root with pinned requirements. Original model scores and original training accuracy remain unavailable. MAPE is an error metric; do not convert it to `100 − MAPE` and call that accuracy.

A separate, newly defined training recipe is in [the model card](MODEL_CARD.md). Its one-epoch export smoke test is recorded separately in [training-smoke.json](training-smoke.json); it is not the preserved model’s training history.

## Checking the earlier 81% claim

No original metric definition, notebook or test split was recovered. The current regression model does not store a classification-accuracy metric in its compile metadata. An 81% claim therefore cannot be confirmed or compared directly. In particular, 100 minus MAPE is not an accuracy score.

Across 376 non-flat next-session moves, the model got **194 correct (51.60%)**. Always predicting up got **189 correct (50.27%)**; repeating the previous daily return got **184 correct (48.94%)**. No threshold was tuned on these results. These are descriptive rates; correlated stocks/days, a small window and unknown pretraining overlap prevent an independent skill claim.

| Symbol | Model direction | Always up | Repeat last return | Model price within 5% | Last close within 5% |
|---|---:|---:|---:|---:|---:|
| AAPL | 46.03% | 53.97% | 42.86% | 0.00% | 98.41% |
| MSFT | 42.86% | 57.14% | 44.44% | 9.52% | 98.41% |
| NVDA | 46.03% | 53.97% | 55.56% | 0.00% | 96.83% |
| RELIANCE.NS | 59.68% | 46.77% | 41.94% | 100.00% | 100.00% |
| SPY | 53.97% | 46.03% | 52.38% | 0.00% | 100.00% |
| TCS.NS | 61.29% | 43.55% | 56.45% | 22.22% | 98.41% |

The last-return baseline forecasts next close as origin close multiplied by the previous observed close-to-close ratio; it uses no target data. Always-up/down references use fixed directions. Flat target moves are excluded from direction rates; they remain in price metrics.

A clearly defined price hit means absolute forecast error is at most 5% of actual close. The model hit **83/378 (21.96%)**, versus **373/378 (98.68%)** for persistence. The 5% cutoff is a descriptive tolerance, not the recovered definition of the old claim. One-percent hit rates are also in the JSON.

The model's mean percentage error is about **11.92 times** the persistence error. Its current pipeline is not a reliable next-session price predictor on these histories. Missing training preprocessing, cross-symbol generalization and genuine out-of-time performance require investigation before replacing the original weights or claiming improvement.

## Source-data check

`python audit_data.py` validates every saved OHLCV row and compares the same date ranges with a fresh Yahoo Finance download. [The full report](../evaluation/data-audit.json) records structural checks, input hashes, exact date/volume comparisons and price differences. All 1,506 rows passed structural checks and all dates/volumes matched. The largest adjusted-price difference was under 0.00026 quote units. Some cells exceeded the strict numerical tolerance, so the report retains those differences instead of declaring a byte-exact match. This verifies same-provider consistency, not original training provenance or independent exchange records.
