# Contributing to Northstar

Northstar is a Streamlit stock-research prototype. Start with [the README](README.md), [model card](docs/MODEL_CARD.md), [evaluation](docs/EVALUATION.md) and [data card](docs/DATA_CARD.md).

## Set up and validate

Use Python 3.12 from the repository root:

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

The primary app needs no API keys. Begin with the saved histories to reproduce a problem without external requests. For UI changes, check desktop and phone layouts, keyboard navigation, both themes and reduced motion. Record the test results and screenshots for the affected behavior in your pull request.

## Choose useful work

Good starting points include clearer setup documentation, reproducible CSV-validation bugs, keyboard-access problems, and failures when news providers are unavailable. Use the bug or feature template to describe the actual behavior, a minimal example and the expected result. Discussions are available for setup questions and explanations.

Keep one coherent improvement per pull request and link its issue. Add tests when changing behavior; documentation-only changes need accurate commands and working references. Credit actual collaborators with their agreed GitHub-associated email in a `Co-authored-by` trailer.

## Preserve reproducibility

Do not overwrite `model3.h5`, reinterpret diagnostic error as accuracy, or present historical scenario bands as validated forecast confidence. The supplied model's original training overlap is unknown. Any new model belongs in a new output directory with its data ranges, chronological partitions, training-only scaler and evaluation recorded.

After changing evaluation inputs or calculations, run `python evaluate.py` and explain the resulting metrics and input hashes. Refreshing saved histories also requires matching provenance and data-audit records. Never introduce visitor-triggered training or unbounded provider requests.

## Data and attribution

Use synthetic or public, redistributable examples in issues. Do not upload credentials, Streamlit Secrets, private portfolios or academic documents. Existing source history may contain old credentials; report sensitive material privately to the maintainer rather than copying it into an issue.

No open-source license has been selected. Read [NOTICE.md](NOTICE.md); third-party data and dependencies retain their own rights. Do not copy complete publisher articles into the repository.
