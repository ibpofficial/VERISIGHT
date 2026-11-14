import json
import urllib.request
import urllib.error

BACKEND_URL = "https://verisight-3ip3.onrender.com"

print(f"Testing backend: {BACKEND_URL}")

# 1. Health probe
try:
    req = urllib.request.Request(f"{BACKEND_URL}/health", headers={"User-Agent": "VERISIGHT-Tester/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("[1] HEALTH CHECK:", data)
except Exception as e:
    print("[1] HEALTH CHECK FAILED:", e)

# 2. Login probe
token = None
try:
    login_payload = json.dumps({"email": "officer@verisight.gov.in", "password": "Officer@12345"}).encode("utf-8")
    req = urllib.request.Request(
        f"{BACKEND_URL}/api/v1/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json", "User-Agent": "VERISIGHT-Tester/1.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        token = data.get("access_token")
        print("[2] LOGIN TEST: SUCCESS! Received access token.")
except Exception as e:
    print("[2] LOGIN TEST FAILED:", e)

# 3. Engine diagnostics probe
if token:
    try:
        req = urllib.request.Request(
            f"{BACKEND_URL}/api/v1/admin/engine-status",
            headers={"Authorization": f"Bearer {token}", "User-Agent": "VERISIGHT-Tester/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("[3] ENGINE DIAGNOSTICS:")
            for eng in data.get("engines", []):
                print(f"    - {eng['name']}: {eng['status']}")
    except Exception as e:
        print("[3] ENGINE DIAGNOSTICS FAILED:", e)

# 4. Quick Check probe
if token:
    try:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="sample_test.txt"\r\n'
            f"Content-Type: text/plain\r\n\r\n"
            f"VERISIGHT Cloud Integration Test Sample Content\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{BACKEND_URL}/api/v1/quick-checks",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "VERISIGHT-Tester/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("[4] QUICK CHECK PROBE: SUCCESS! Check ID:", data.get("id"))
    except Exception as e:
        print("[4] QUICK CHECK PROBE FAILED:", e)

