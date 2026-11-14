#!/usr/bin/env python3
"""
VERISIGHT System Smoke Test Suite
Executes live end-to-end integration probes across all services, engines, and APIs using standard library urllib.
Exits 0 on all passing, 1 on any failure.
"""

import sys
import os
import time
import json
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "PASS": "\033[92m",
        "FAIL": "\033[91m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}[{status}] {msg}{colors['RESET']}")

def request(method, path, json_data=None, headers=None):
    url = f"{BASE_URL}{path}"
    req_headers = headers.copy() if headers else {}
    req_data = None

    if json_data is not None:
        req_data = json.dumps(json_data).encode('utf-8')
        req_headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            res_body = response.read().decode('utf-8')
            try:
                parsed = json.loads(res_body)
            except Exception:
                parsed = res_body
            return response.status, parsed
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = err_body
        return e.code, parsed

def main():
    print("=" * 65)
    print("      VERISIGHT PRODUCTION INTEGRATION SMOKE TEST SUITE       ")
    print("=" * 65)

    tests_run = 0
    tests_passed = 0

    def record(name, passed, detail=""):
        nonlocal tests_run, tests_passed
        tests_run += 1
        if passed:
            tests_passed += 1
            log(f"{name}: PASS {detail}", "PASS")
        else:
            log(f"{name}: FAIL {detail}", "FAIL")

    # 1. Health Probe
    try:
        status, body = request("GET", "/health")
        record("System Health Endpoint", status == 200 and body.get("status") == "HEALTHY", f"HTTP {status}")
    except Exception as e:
        record("System Health Endpoint", False, str(e))

    # 2. Authentication Probe
    token = None
    try:
        status, body = request("POST", "/api/v1/auth/login", json_data={"email": "admin@verisight.gov.in", "password": "Admin@12345"})
        passed = status == 200 and "access_token" in body
        if passed:
            token = body["access_token"]
        record("Admin/Officer Authentication", passed, f"Token generated ({len(token) if token else 0} chars)")
    except Exception as e:
        record("Admin/Officer Authentication", False, str(e))

    auth_headers = {"Authorization": f"Bearer {token}"} if token else {}

    # 3. Cryptographic Audit Chain Integrity Probe
    try:
        status, body = request("GET", "/api/v1/audit/verify-integrity", headers=auth_headers)
        passed = status == 200 and body.get("is_intact") is True
        record("SHA-256 Ledger Integrity", passed, f"Total blocks: {body.get('total_blocks_verified', 0)}")
    except Exception as e:
        record("SHA-256 Ledger Integrity", False, str(e))

    # 4. Admin Diagnostics & Engine Self-Test Probe
    try:
        status, body = request("GET", "/api/v1/admin/self-test", headers=auth_headers)
        passed = status == 200 and body.get("status") == "SYSTEM_OPERATIONAL"
        if not passed:
            print("SELF-TEST DEBUG BODY:", status, body)
        record("Core Subsystems Diagnostics", passed, f"Latency: {body.get('total_latency_ms')}ms")
    except Exception as e:
        record("Core Subsystems Diagnostics", False, str(e))

    # 5. Case Queue & Database Query Probe
    try:
        status, body = request("GET", "/api/v1/cases", headers=auth_headers)
        passed = status == 200 and isinstance(body, list)
        record("Investigation Case Queue", passed, f"{len(body)} active cases retrieved")
    except Exception as e:
        record("Investigation Case Queue", False, str(e))

    # 6. Dashboard Live Metrics Probe
    try:
        status, body = request("GET", "/api/v1/dashboard/stats", headers=auth_headers)
        passed = status == 200 and "metrics" in body
        record("Dashboard Live DB Aggregations", passed, f"Total screenings: {body.get('metrics', {}).get('total_screenings', 0)}")
    except Exception as e:
        record("Dashboard Live DB Aggregations", False, str(e))

    # Final Summary Table
    print("\n" + "=" * 65)
    print(f"SUMMARY: {tests_passed}/{tests_run} Probes Succeeded ({(tests_passed/tests_run)*100:.1f}%)")
    print("=" * 65)

    if tests_passed == tests_run:
        print("\033[92mALL INTEGRATION PROBES PASSED SUCCESSFULLY.\033[0m\n")
        sys.exit(0)
    else:
        print("\033[91mONE OR MORE INTEGRATION PROBES FAILED.\033[0m\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
