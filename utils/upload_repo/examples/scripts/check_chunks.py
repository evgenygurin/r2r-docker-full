#!/usr/bin/env python3
"""Check document chunks"""
import requests
import json

API_URL = "http://136.119.36.216:7272"
TOKEN_FILE = "/tmp/r2r_token.txt"

# Read token
with open(TOKEN_FILE, 'r') as f:
    token = f.read().strip()

headers = {
    "Authorization": f"Bearer {token}"
}

# Check chunks for config.py (already processed)
doc_id = "c78475b4-ddfd-5896-9aa4-26a002dca7d4"

print(f"Checking chunks for document {doc_id} (config.py)...\n")

response = requests.get(
    f"{API_URL}/v3/documents/{doc_id}/chunks",
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    chunks = result.get('results', [])

    print(f"Total chunks: {len(chunks)}\n")
    print("=" * 70)

    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk #{i}:")
        print(f"  Chunk ID: {chunk.get('id', 'N/A')}")

        # Check text content
        text = chunk.get('text', '')
        print(f"  Text preview: {text[:150]}...")

        # Check metadata
        metadata = chunk.get('metadata', {})
        if metadata:
            print(f"  Metadata:")
            for key, value in metadata.items():
                if key not in ['text', 'extraction_id']:
                    print(f"    {key}: {value}")

        print("  " + "-" * 66)

    # Analysis
    print("\n" + "=" * 70)
    print("АНАЛИЗ РАЗБИЕНИЯ:")
    print("=" * 70)

    # Check if chunks contain function/class names
    function_keywords = ['def ', 'class ', '__init__', 'return']
    import_keywords = ['import ', 'from ']

    chunks_with_functions = sum(1 for c in chunks if any(kw in c.get('text', '') for kw in function_keywords))
    chunks_with_imports = sum(1 for c in chunks if any(kw in c.get('text', '') for kw in import_keywords))

    print(f"✓ Chunks с функциями/классами: {chunks_with_functions}/{len(chunks)}")
    print(f"✓ Chunks с импортами: {chunks_with_imports}/{len(chunks)}")

    # Check average chunk size
    avg_size = sum(len(c.get('text', '')) for c in chunks) / len(chunks) if chunks else 0
    print(f"✓ Средний размер chunk: {int(avg_size)} символов")

    # Validation
    print("\nВАЛИДАЦИЯ:")
    if chunks_with_functions > 0:
        print("✓ PASS: Код разбит по функциям/классам")
    else:
        print("✗ FAIL: Функции/классы не обнаружены в chunks")

    if chunks_with_imports > 0:
        print("✓ PASS: Импорты выделены в отдельные chunks")
    else:
        print("⚠ WARNING: Импорты не найдены (возможно в других chunks)")

else:
    print(f"✗ Failed to get chunks: {response.status_code}")
    print(f"Response: {response.text}")
