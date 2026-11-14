import urllib.request
import json
import time

# 1. Login
login_payload = json.dumps({"email": "officer@verisight.gov.in", "password": "Officer@12345"}).encode("utf-8")
req = urllib.request.Request(
    "https://verisight-3ip3.onrender.com/api/v1/auth/login",
    data=login_payload,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
token = json.loads(resp.read().decode("utf-8"))["access_token"]
print("Auth token acquired.")

# 2. Prepare sample image upload
import cv2
import numpy as np

img = np.ones((600, 800, 3), dtype=np.uint8) * 220
cv2.putText(img, "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<", (30, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
cv2.putText(img, "Z4819201<4IND9205142M3205148<<<<<<<<<<<<<<<4", (30, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
_, img_bytes = cv2.imencode(".jpg", img)

boundary = "----WebKitFormBoundaryTest123456"
body = bytearray()
body.extend(f"--{boundary}\r\n".encode("utf-8"))
body.extend(b'Content-Disposition: form-data; name="file"; filename="sample_passport.jpg"\r\n')
body.extend(b"Content-Type: image/jpeg\r\n\r\n")
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

