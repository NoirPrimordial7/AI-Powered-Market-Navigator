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
