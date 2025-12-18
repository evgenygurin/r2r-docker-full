#!/usr/bin/env python3
"""Test Knowledge Graph - v2 with collection ID"""
import requests
import json

API_URL = "http://136.119.36.216:7272"
TOKEN_FILE = "/tmp/r2r_token.txt"
COLLECTION_FILE = "/tmp/collection_id.txt"

with open(TOKEN_FILE, 'r') as f:
    token = f.read().strip()

with open(COLLECTION_FILE, 'r') as f:
    collection_id = f.read().strip()

headers = {"Authorization": f"Bearer {token}"}

print("="*70)
print("ШАГ 4: ПРОВЕРКА KNOWLEDGE GRAPH ДЛЯ КОДА")
print("="*70)
print(f"\nCollection ID: {collection_id}")

# Check if graph already exists
print("\n1. Проверка существующего графа...")

entities_response = requests.get(
    f"{API_URL}/v3/graphs/{collection_id}/entities",
    headers=headers,
    params={"limit": 100}
)

print(f"Entities endpoint status: {entities_response.status_code}")

if entities_response.status_code == 200:
    entities_result = entities_response.json()
    entities = entities_result.get('results', [])

    print(f"✓ Найдено entities: {len(entities)}")

    if len(entities) > 0:
        print("\nTop entities:")
        for i, entity in enumerate(entities[:15], 1):
            entity_name = entity.get('name', 'N/A')
            entity_type = entity.get('category', entity.get('description', 'N/A')[:30])
            print(f"  {i}. {entity_name} ({entity_type})")

        # Get relationships
        print("\n2. Получение relationships...")

        rel_response = requests.get(
            f"{API_URL}/v3/graphs/{collection_id}/relationships",
            headers=headers,
            params={"limit": 100}
        )

        if rel_response.status_code == 200:
            rel_result = rel_response.json()
            relationships = rel_result.get('results', [])

            print(f"✓ Найдено relationships: {len(relationships)}")

            if len(relationships) > 0:
                print("\nTop relationships:")
                for i, rel in enumerate(relationships[:15], 1):
                    subject = rel.get('subject', 'N/A')
                    predicate = rel.get('predicate', 'N/A')
                    obj = rel.get('object', 'N/A')
                    print(f"  {i}. {subject} --[{predicate}]--> {obj}")

            # Validation
            print("\n" + "="*70)
            print("ВАЛИДАЦИЯ:")
            print("="*70)

            # Check for code-specific patterns
            entity_names = [e.get('name', '') for e in entities]
            entity_str = ' '.join(entity_names).lower()

            has_classes = any(name in entity_str for name in ['authenticationmanager', 'databasemanager', 'appconfig'])
            has_functions = any(name in entity_str for name in ['authenticate', 'hash_password', 'generate_token'])
            has_modules = any(name in entity_str for name in ['auth', 'database', 'config'])

            if has_classes:
                print("✓ PASS: Классы (AuthenticationManager, DatabaseManager) найдены")
            else:
                print("⚠ WARNING: Классы не найдены в entities")

            if has_functions:
                print("✓ PASS: Функции (authenticate_user, hash_password) найдены")
            else:
                print("⚠ WARNING: Функции не найдены")

            if has_modules:
                print("✓ PASS: Модули (auth, database, config) найдены")
            else:
                print("⚠ WARNING: Модули не найдены")

            if len(relationships) > 0:
                print("✓ PASS: Relationships существуют")

                # Check for specific relationship types
                rel_types = [r.get('predicate', '') for r in relationships]
                rel_str = ' '.join(rel_types).lower()

                if 'calls' in rel_str or 'uses' in rel_str or 'imports' in rel_str:
                    print("✓ PASS: Code-specific relationships (calls/uses/imports)")
                else:
                    print("⚠ INFO: Relationship types:", set(rel_types[:10]))
            else:
                print("✗ FAIL: Relationships не найдены")

        else:
            print(f"✗ Failed to get relationships: {rel_response.status_code}")

    else:
        print("\n⚠ WARNING: Граф пустой - возможно нужно запустить extraction")
        print("\nДля создания графа используйте:")
        print(f"POST {API_URL}/v3/graphs/{collection_id}/extract")

else:
    print(f"✗ Failed: {entities_response.status_code}")
    print(entities_response.text[:500])
