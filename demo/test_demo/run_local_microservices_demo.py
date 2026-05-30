"""Start a local mock product catalog and the recommendation service so the
`run_prd_grpc_validation.py` demo can connect to a live endpoint.

Usage:
  .\.venv\Scripts\python.exe demo/test_demo/run_local_microservices_demo.py

This will:
- Spawn `mock_product_catalog_server.py` on port 3560
- Spawn `recommendation_server.py` with `PRODUCT_CATALOG_SERVICE_ADDR=localhost:3560` and `PORT=3550`

Both processes run in foreground in this script; press Ctrl+C to stop both.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

mock = ROOT / "demo" / "test_demo" / "mock_product_catalog_server.py"
rec = ROOT / "demo" / "test_demo" / "microservices-demo" / "src" / "recommendationservice" / "recommendation_server.py"

env = dict(**os.environ) if 'os' in globals() else None
if env is None:
    import os
    env = dict(**os.environ)

# Start mock product catalog
print("Starting mock ProductCatalogService on localhost:3560")
proc_mock = subprocess.Popen([PY, str(mock)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
# Allow mock to start
time.sleep(1)
# Tail mock stdout asynchronously

# Start recommendation service pointing to mock
print("Starting recommendationservice on localhost:3550 (PRODUCT_CATALOG_SERVICE_ADDR=localhost:3560)")
env_rec = dict(env)
env_rec["PRODUCT_CATALOG_SERVICE_ADDR"] = "localhost:3560"
env_rec["PORT"] = "3550"
proc_rec = subprocess.Popen([PY, str(rec)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env_rec)

print(f"Mock PID: {proc_mock.pid}, Recommendation PID: {proc_rec.pid}")
print("Tailing logs. Press Ctrl+C to stop.")
try:
    while True:
        line = proc_mock.stdout.readline()
        if line:
            print("[mock]", line.rstrip())
        line = proc_rec.stdout.readline()
        if line:
            print("[rec]", line.rstrip())
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Stopping processes...")
    proc_rec.terminate()
    proc_mock.terminate()
    proc_rec.wait()
    proc_mock.wait()
    print("Stopped.")
