#!/usr/bin/env python3
import requests

TOKEN = open('/tmp/r2r_token.txt').read().strip()
COLLECTION = open('/tmp/collection_id.txt').read().strip()

response = requests.post(
    f"http://136.119.36.216:7272/v3/graphs/{COLLECTION}/pull",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json=True  # Force re-pull
)

print(f"Status: {response.status_code}")
print(response.text)
