import urllib.request
import json
import time
import numpy as np
import cv2

# Login
login_payload = json.dumps({"email": "officer@verisight.gov.in", "password": "Officer@12345"}).encode("utf-8")
req = urllib.request.Request(
    "https://verisight-3ip3.onrender.com/api/v1/auth/login",
    data=login_payload,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
token = json.loads(resp.read().decode("utf-8"))["access_token"]
print("Auth token acquired.")

# Regular image without MRZ (like og-image.png)
img = np.zeros((400, 800, 3), dtype=np.uint8)
cv2.putText(img, "VERISIGHT DEMO SCREEN", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
_, img_bytes = cv2.imencode(".png", img)

boundary = "----WebKitFormBoundaryOgImage"
body = bytearray()
body.extend(f"--{boundary}\r\n".encode("utf-8"))
body.extend(b'Content-Disposition: form-data; name="file"; filename="og-image.png"\r\n')
body.extend(b"Content-Type: image/png\r\n\r\n")
body.extend(img_bytes.tobytes())
body.extend(b"\r\n")

body.extend(f"--{boundary}\r\n".encode("utf-8"))
body.extend(b'Content-Disposition: form-data; name="document_type"\r\n\r\n')
body.extend(b"PASSPORT_TD3\r\n")

body.extend(f"--{boundary}\r\n".encode("utf-8"))
body.extend(b'Content-Disposition: form-data; name="issuing_country_code"\r\n\r\n')
body.extend(b"IND\r\n")

body.extend(f"--{boundary}--\r\n".encode("utf-8"))

req2 = urllib.request.Request(
    "https://verisight-3ip3.onrender.com/api/v1/screenings",
    data=bytes(body),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
)

t0 = time.time()
try:
    with urllib.request.urlopen(req2, timeout=60) as resp2:
        print("Screening created successfully in", round(time.time() - t0, 2), "s")
        print("Response:", resp2.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.read().decode("utf-8"))
except Exception as e:
    print("ERROR:", e)

