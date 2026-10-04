# Public deployment

Use Streamlit Community Cloud for this Python/TensorFlow app. A Vercel static site can later serve the portfolio and link to it; moving TensorFlow inference into Vercel requires a different service architecture. The small model can stay in this GitHub repository; Hugging Face model hosting alone does not supply an inference server for a custom Keras artifact.

## Configuration

- Repository: `NoirPrimordial7/AI-Powered-Market-Navigator`
- Branch: `main`
- Entrypoint: `app.py`
- Python: **3.12**, selected in advanced settings
- Dependencies: `requirements.txt`
- Secrets: **none needed** for saved/live studies, uploaded CSV analysis or public publisher feeds
- Optional sentiment: fresh credentials through Streamlit Secrets; use `.streamlit/secrets.example.toml` as a template

Follow [Streamlit's deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy). Public app URL must be recorded after deployment succeeds and is verified; a desired subdomain is not a confirmed live URL.

## Demo limits

Analysis, ticker-news, sentiment and watchlist load/comparison requests are limited to five actions per minute per Streamlit session and 120 per hour across this instance. One watchlist action handles at most eight symbols. Histories/inference cache for 15 minutes, sentiment for 30 minutes. Model execution uses a shared lock. There are no paid LLM calls or visitor-triggered training jobs.

These bounds are useful for an interview demo. They are not authentication, IP-based enforcement or a distributed abuse-prevention system: a new browser session changes its identity; the instance-wide cap remains. Filesystem counters can reset on restarts or ephemeral hosts. Multiple replicas require a shared persistent rate-limit store. Public quotes/news depend on provider availability and their own usage limits.

Community Cloud apps can sleep when idle and may need to wake before an interview. Free hosting has resource limits; a working local build is not proof of cloud availability. Set no paid service or autoscaling subscription merely to keep this portfolio demo online.

## Release checks

Run `python -m pip check` and `python -m unittest discover -s tests -v`. CI mirrors these checks on Linux/Python 3.12 and verifies the original model hash. Page tests use deterministic offline feed results; feed parser/outage/relevance tests mock network results. A passing CI run proves the tested paths, not prediction quality or uninterrupted upstream availability.

Review the release manifest; exclude environments, caches, actual secrets, private PDFs/Drive files and unrelated original backups. The old public source contained hardcoded credentials. They must be revoked with their providers; replacing current files does not revoke keys or remove them from Git history.

To roll back code, deploy an earlier reviewed commit. Keep the original model hash unchanged unless explicitly releasing a separately documented model version.
