"""Wait for the packaged Streamlit server's HTTP health endpoint."""
import time
import urllib.request

for attempt in range(60):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health',timeout=2) as response:
            if response.status==200 and response.read().strip()==b'ok':
                print('Packaged Streamlit HTTP health check passed')
                break
    except (OSError,ValueError):pass
    time.sleep(1)
else:raise SystemExit('Packaged Streamlit server did not become healthy')
