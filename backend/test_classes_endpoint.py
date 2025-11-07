#!/usr/bin/env python3
"""
Test script for /admin/school/classes endpoint
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1"

# Login as school admin
login_response = requests.post(
    f"{API_URL}/auth/login",
    json={
        "email": "admin@school1.com",
        "password": "admin123"
    }
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

access_token = login_response.json()["access_token"]
print(f"✅ Login successful. Token: {access_token[:20]}...")

# Test /admin/school/classes endpoint
headers = {"Authorization": f"Bearer {access_token}"}
classes_response = requests.get(f"{API_URL}/admin/school/classes", headers=headers)

print(f"\nGET /admin/school/classes")
print(f"Status: {classes_response.status_code}")
print(f"Response: {json.dumps(classes_response.json(), indent=2)}")
