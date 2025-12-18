#!/usr/bin/env python3
"""Check document processing status"""
import requests
import json
import time

API_URL = "http://136.119.36.216:7272"
TOKEN_FILE = "/tmp/r2r_token.txt"
DOC_IDS_FILE = "/tmp/document_ids.txt"

# Read token
with open(TOKEN_FILE, 'r') as f:
    token = f.read().strip()

# Read document IDs
with open(DOC_IDS_FILE, 'r') as f:
    doc_ids = [line.strip() for line in f if line.strip()]

headers = {
    "Authorization": f"Bearer {token}"
}

print("Checking document status...\n")

for doc_id in doc_ids:
    response = requests.get(
        f"{API_URL}/v3/documents/{doc_id}",
        headers=headers
    )

    if response.status_code == 200:
        result = response.json()['results']
        print(f"Document ID: {doc_id}")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  Type: {result.get('document_type', 'N/A')}")
        print(f"  Ingestion Status: {result.get('ingestion_status', 'N/A')}")
        print(f"  Extraction Status: {result.get('extraction_status', 'N/A')}")

        metadata = result.get('metadata', {})
        if metadata:
            print(f"  Language: {metadata.get('language', 'N/A')}")
            print(f"  Module: {metadata.get('module', 'N/A')}")
        print()
    else:
        print(f"✗ Failed to get {doc_id}: {response.status_code}")
        print(f"  {response.text}\n")

print("=" * 50)
