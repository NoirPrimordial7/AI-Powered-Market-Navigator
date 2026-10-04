# Releases and container package

Maintainer: **Aditya Gholap · NoirPrimordial7**. The first release is **v1.0.0**; its app version is `1.0.0` in `VERSION`.

- [Live studio](https://northstar-aditya-gholap.streamlit.app/)
- [Versioned releases](https://github.com/NoirPrimordial7/AI-Powered-Market-Navigator/releases)
- Registry image: `ghcr.io/noirprimordial7/ai-powered-market-navigator`

## Use the container

The published image targets **Linux/amd64**, uses Python 3.12 and runs as UID 10001. Docker Desktop on Windows must use Linux containers. Apple Silicon can use amd64 emulation; no native arm64 image is claimed.

```sh
docker pull ghcr.io/noirprimordial7/ai-powered-market-navigator:1.0.0
docker run --rm -p 127.0.0.1:8501:8501 ghcr.io/noirprimordial7/ai-powered-market-navigator:1.0.0
```

Open `http://localhost:8501`. The primary app requires no API key. The `latest` tag tracks the newest published stable release; use a version tag, or the registry digest shown on its package page, to select an artifact explicitly. Runtime caches and rate-limit counters are ephemeral. Multiple replicas do not share a distributed limiter. Do not treat this interview demo as a production trading service.

For optional integrations, pass fresh environment variables at runtime using Docker's `--env-file` option. Never put credentials in a Dockerfile, image, build argument, archive or committed file. The container contains the original model, saved histories, evaluation results, documentation and tests. It contains no local cache, environment, real Streamlit secrets or private academic documents.

## Source archive integrity

Each release provides `northstar-v1.0.0.zip`, `SHA256SUMS.txt` and `release-manifest.json`. The manifest records the source commit, per-file size and SHA-256, archive SHA-256 and original model hash. These checks detect accidental changes; they are not a cryptographic signature or evidence of original training provenance.

```sh
sha256sum -c SHA256SUMS.txt
```

On PowerShell, compare `(Get-FileHash .\northstar-v1.0.0.zip -Algorithm SHA256).Hash` with the checksum file. The original `model3.h5` SHA-256 is:

```text
73d8c9649771a76c1c9f3b83dba24cba140b7ea1a349055f43f9374eea4e04c1
```

The ZIP is deterministic for the same included file bytes. Container builds can vary as the base image and dependency registry change; the published digest identifies the actual built image.

## Maintainer publication process

1. Update `VERSION` and `CHANGELOG.md`; review only the intended public files.
2. Run `python -m pip check` and `python -m unittest discover -s tests -v`. Push the reviewed source and wait for both Linux verification and container jobs in `checks.yml` to succeed.
3. Build assets from that exact source commit: `python scripts/build_release.py --version v1.0.0 --revision FULL_40_CHARACTER_COMMIT_SHA`. The builder validates the version/model and stops on recognized credential patterns or nonempty example secrets. Detection is an additional check, not a guarantee that every possible secret type is recognized.
4. Create the GitHub release targeting that commit and attach all three files from `dist/` before publishing. Describe model limitations and link the source/evaluation documents.
5. `publish.yml` runs on a published release, builds the container, executes its tests and checks HTTP health before logging in and pushing version/latest tags. It uses the short-lived workflow `GITHUB_TOKEN` with repository read and package write permissions; no personal token or app API key is needed.
6. Verify the package is public and linked to this repository, and verify the workflow result and registry digest. A release page alone does not prove the package job succeeded.

## Historical secret alert

The reported OpenRouter key was exposed in historical `demo1.py`. Current code does not use OpenRouter and contains no embedded OpenRouter credential. Old commits, forks and other copies can still expose the old value, so revocation is necessary even after removing the source file. The owner must revoke the key at [OpenRouter's key settings](https://openrouter.ai/settings/keys), inspect provider usage/billing for unauthorized activity, and only then close the GitHub alert as **revoked**. Do not test a leaked key against the provider or mark it as a false positive merely because current files are clean.

This release does not claim that old history was erased or that provider revocation has been independently verified. See [NOTICE](../NOTICE.md) for copyright and [DATA_CARD](DATA_CARD.md) for provider rights. No open-source license has been selected.
