# Preserved model: model3.h5

Maintainer: **Aditya Gholap · NoirPrimordial7**. This is an educational research demonstration, not an investment recommendation or validated trading system.

## What is verified

The HDF5 artifact is unchanged from the supplied E-drive and F-drive versions. SHA-256:

```
73d8c9649771a76c1c9f3b83dba24cba140b7ea1a349055f43f9374eea4e04c1
```

The serialized model records Keras 3.6.0, a TensorFlow backend, input `(None, 30, 11)`, and one linear scalar output. Its layers are:

| Layer | Configuration |
|---|---|
| Bidirectional LSTM | 128 units per direction, concatenation, return sequences |
| Dropout | 0.30 |
| GRU | 64 units, return sequences |
| Dropout | 0.30 |
| LSTM | 32 units, final sequence output |
| Dropout | 0.20 |
| Dense | 1 unit, linear |

The saved compile configuration records **mean squared error** and **Adam**, learning rate approximately **0.001**, beta₁ 0.9, beta₂ 0.999, epsilon 1e-7. This is compile metadata, not an epoch log or proof of the training data used.

The original inference source uses the feature order `Open, High, Low, Close, Volume, RSI, SMA_20, MACD, MACD_signal, BB_upper, BB_lower`. The artifact confirms the count of 11 features but does not independently encode their semantic names. The app preserves the original source's order and treats the scalar output as scaled closing price.

## Current inference

1. Validate or retrieve daily OHLCV data.
2. Compute causal RSI 14, SMA 20, MACD 12/26 with signal 9, and Bollinger Bands 20 with two standard deviations using `ta`.
3. Select the original 11 columns; forward-fill indicator gaps and fill initial remaining gaps with zero, matching the recovered app's convention.
4. Fit MinMax scaling on the currently available history. Pass only its latest **30 sessions** to the model. The old source's full-year tensor did not match the trained input shape.
5. Apply inverse scaling to the Close column. Reject nonfinite or nonpositive estimates.

SMA 50, returns, drawdown, simulations, headlines and optional sentiment are displayed independently and do not enter this model. Future dates exclude weekends but not exchange holidays.

## Missing original training evidence

The original notebook, raw training dataset, exact symbols/date ranges, target horizon, original scaler, train/validation/test boundaries, epoch count, batch size, random seed, learning curves and original evaluation scores have **not been recovered**. Recovered academic reports discuss a proposed workflow; they do not establish an executed training run. See [recovery evidence](RECOVERY.md).

Consequently, the weights cannot be reproduced exactly and original training accuracy cannot be calculated from the artifact alone. The app's next-session interpretation and per-history scaling may differ from the missing training pipeline. Never describe a diagnostic backtest as verified out-of-sample performance while training overlap is unknown.

## Measured performance

[The evaluation report](EVALUATION.md) compares the current pipeline with persistence over 63 next-session targets for each of six saved histories, **378 predictions**. Mean per-symbol MAPE is **14.89%** for the model and **1.25%** for persistence. Every symbol's model MAPE exceeds its baseline. These findings support keeping the model explicitly experimental; they do not establish its performance with the original scaler.

No classification accuracy, confidence score, calibrated interval or causal news effect is claimed. MAPE is an error measure, not `100 − MAPE` accuracy. Poor results are reported rather than removed.

## A reproducible new training recipe

[`training.py`](../training.py) supplies a **new** recipe with the serialized architecture, fresh weights, chronological 70/15/15 row partitions, a scaler fitted only on the training partition, next-session Close targets, seed 42, batch size 32, Adam 0.001, MSE, and validation-loss early stopping with patience 10. It drops the initial indicator warm-up rows and does not shuffle examples. Validation/test windows may include already observed earlier context; their targets remain disjoint. It saves a new `.keras` model, scaler JSON, learning curves/run metadata and test predictions in a new directory.

```sh
python training.py --csv data/AAPL.csv --output training-runs/aapl-v1 --epochs 100
```

This is not the original training procedure and does not replace `model3.h5`. A one-epoch smoke run verifies training/export mechanics; it is not model selection or a new production-quality model. Use a larger appropriately licensed dataset and independently chosen, chronologically separated test period for a serious new experiment. Exact numerical reproducibility can depend on TensorFlow hardware and kernels.
