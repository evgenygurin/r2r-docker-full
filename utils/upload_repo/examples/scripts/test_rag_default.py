#!/usr/bin/env python3
"""Test RAG with default model"""
import requests

API_URL = "http://136.119.36.216:7272"
TOKEN = open('/tmp/r2r_token.txt').read().strip()

headers = {"Authorization": f"Bearer {TOKEN}"}

print("Testing RAG with default model...")

payload = {
    "query": "What authentication methods are used in this code?",
    # Try without rag_generation_config to use default
}

response = requests.post(
    f"{API_URL}/v3/retrieval/rag",
    headers=headers,
    json=payload
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")
