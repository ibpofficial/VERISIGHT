import httpx
import time
import os

base_url = 'http://127.0.0.1:8000/api/v1'

client = httpx.Client(timeout=30.0)

# 1. Login
login_res = client.post(
    f'{base_url}/auth/login',
    json={'email': 'officer@verisight.gov.in', 'password': 'Officer@12345'}
)
print('Login status:', login_res.status_code)
if login_res.status_code != 200:
    print('Login error:', login_res.text)
    exit(1)

token = login_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 2. Upload demo passport
img_path = 'd:/metad/VERISIGHT/demo_passport_sample.jpg'
with open(img_path, 'rb') as f:
    files = {'file': ('demo_passport_sample.jpg', f, 'image/jpeg')}
    data = {
        'document_type': 'PASSPORT',
        'issuing_country_code': 'IND',
        'is_synthetic': 'false',
        'sync': 'false'
    }
    upload_res = client.post(f'{base_url}/screenings', headers=headers, files=files, data=data)

print('Upload status:', upload_res.status_code)
if upload_res.status_code != 200:
    print('Upload error:', upload_res.text)
    exit(1)

screening = upload_res.json()
sc_id = screening['id']
ref_no = screening['reference_no']
print(f'Screening created: ID={sc_id}, Ref={ref_no}')

# 3. Poll status
for attempt in range(30):
    time.sleep(1)
    status_res = client.get(f'{base_url}/screenings/{sc_id}/status', headers=headers)
    if status_res.status_code != 200:
        print('Status fetch error:', status_res.text)
        break
    s = status_res.json()
    print(f"Attempt {attempt+1}: Status={s['status']}, Progress={s['overall_progress']}%, CurrentStage={s['current_stage']}")
    if s['status'] in ('COMPLETED', 'REJECTED_POOR_QUALITY', 'FAILED', 'ABORTED'):
        break

# 4. Fetch full screening details
detail_res = client.get(f'{base_url}/screenings/{sc_id}', headers=headers)
det = detail_res.json()
print('\n=== Screening Results ===')
print('Status:', det.get('status'))
print('Risk Level:', det.get('risk_level'))
print('Total Risk Score:', det.get('total_risk_score'))
print('Extracted Fields Count:', len(det.get('extracted_fields', [])))
for field in det.get('extracted_fields', []):
    print(f"  - {field.get('field_name')}: {field.get('field_value')} (confidence: {field.get('confidence')})")

print('Forensics Findings Count:', len(det.get('forensic_findings', [])))
