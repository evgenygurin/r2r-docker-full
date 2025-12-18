#!/usr/bin/env python3
"""Ingest code files into R2R"""
import requests
import json
import os

API_URL = "http://136.119.36.216:7272"
TOKEN_FILE = "/tmp/r2r_token.txt"
CODE_DIR = "/tmp/test-code"

# Read token
with open(TOKEN_FILE, 'r') as f:
    token = f.read().strip()

headers = {
    "Authorization": f"Bearer {token}"
}

# Upload each Python file
files_to_upload = ['auth.py', 'database.py', 'config.py']
document_ids = []

for filename in files_to_upload:
    filepath = os.path.join(CODE_DIR, filename)

    with open(filepath, 'rb') as f:
        files = {'file': (filename, f, 'text/x-python')}
        metadata = {
            'source': 'codebase',
            'language': 'python',
            'module': filename.replace('.py', '')
        }

        response = requests.post(
            f"{API_URL}/v3/documents",
            headers=headers,
            files=files,
            data={'metadata': json.dumps(metadata)}
        )

        # 202 Accepted означает задача в очереди - это нормально
        if response.status_code in [200, 201, 202]:
            result = response.json()
            doc_id = result['results']['document_id']
            task_id = result['results'].get('task_id', 'N/A')
            document_ids.append(doc_id)
            print(f"✓ Uploaded {filename}")
            print(f"  Document ID: {doc_id}")
            print(f"  Task ID: {task_id}")
        else:
            print(f"✗ Failed {filename}: {response.status_code}")
            print(f"  Response: {response.text}")

# Save document IDs for later use
with open('/tmp/document_ids.txt', 'w') as f:
    f.write('\n'.join(document_ids))

print(f"\n{'='*50}")
print(f"Total uploaded: {len(document_ids)}")
print(f"Document IDs saved to /tmp/document_ids.txt")
