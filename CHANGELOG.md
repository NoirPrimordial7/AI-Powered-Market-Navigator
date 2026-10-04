# Changelog

## v1.0.0 — 2026-10-05

First versioned Northstar release by Aditya Gholap (NoirPrimordial7).

- Editorial overview, compact research studio with a floating study editor, and a separate comparison view. View switches bring the selected content into sight.
- Six saved stock histories, validated CSV uploads, requested live data, price and risk charts, publisher-linked headlines, watchlists and reproducible historical scenarios.
- Original model preserved with its SHA-256; model/data cards, source audit, all 378 diagnostic predictions and an independently defined training recipe.
- Honest experimental results: 14.89% macro MAPE and 51.60% direction accuracy. Original training overlap is unknown; these are not verified holdout scores and do not reproduce the earlier 81% claim.
- Session/instance request limits and caches; no paid LLM calls or public training jobs.
- Allowlisted source ZIP, per-file hash manifest, checksum file and a non-root Linux/amd64 container. CI verifies tests, original-model integrity and the container's HTTP service before publication.

Historical credentials are absent from the current source and distribution. Removing files does not revoke keys exposed in old commits: affected keys must be revoked with their providers. Copyright, academic contributors and provider terms remain documented in NOTICE.md and docs/DATA_CARD.md.
