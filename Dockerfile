FROM python:3.12-slim-bookworm

ARG APP_VERSION=1.0.0
ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="Northstar / AI-Powered Market Navigator" \
      org.opencontainers.image.description="Independent stock research studio with experimental model inference" \
      org.opencontainers.image.authors="Aditya Gholap (NoirPrimordial7)" \
      org.opencontainers.image.source="https://github.com/NoirPrimordial7/AI-Powered-Market-Navigator" \
      org.opencontainers.image.url="https://northstar-aditya-gholap.streamlit.app/" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="Proprietary; see NOTICE.md and provider terms"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_NUM_INTRAOP_THREADS=2 \
    TF_NUM_INTEROP_THREADS=1 \
    HOME=/home/northstar

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 northstar
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt && python -m pip check
COPY app.py market.py news.py research.py ui.py audit_data.py evaluate.py training.py prepare_data.py ./
COPY model3.h5 VERSION README.md NOTICE.md CHANGELOG.md Dockerfile .dockerignore ./
COPY assets ./assets
COPY pages ./pages
COPY data ./data
COPY evaluation ./evaluation
COPY docs ./docs
COPY tests ./tests
COPY scripts ./scripts
COPY .github/workflows ./.github/workflows
COPY .streamlit/config.toml .streamlit/secrets.example.toml ./.streamlit/
COPY .gitignore .gitattributes ./
RUN mkdir -p .cache .tmp training-runs dist \
    && chown northstar:northstar .cache .tmp training-runs dist
USER northstar
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
