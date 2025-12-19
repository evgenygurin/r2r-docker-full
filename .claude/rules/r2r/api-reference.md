# R2R API Reference

## API Endpoints Overview

Base URL: `http://localhost:7272` (local) or `https://your-domain.com` (production)

API Version: v3

## Authentication

### Login

**Endpoint:** `POST /v3/users/login`

**curl:**
```bash
curl -X POST http://localhost:7272/v3/users/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

**Python:**
```python
from r2r import R2RClient

client = R2RClient("http://localhost:7272")
response = client.users.login("user@example.com", "password")

# Response includes access_token and refresh_token
print(response["access_token"]["token"])
```

**Response:**
```json
{
  "access_token": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
  },
  "refresh_token": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
  }
}
```

### Register

**Endpoint:** `POST /v3/users/register`

**curl:**
```bash
curl -X POST http://localhost:7272/v3/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepassword123"
  }'
```

**Python:**
```python
response = client.users.register(
    email="newuser@example.com",
    password="securepassword123"
)
```

### Use Token in Requests

**curl:**
```bash
curl -H "Authorization: Bearer eyJhbGci..." \
  http://localhost:7272/v3/users/me
```

**Python:**
```python
# Token is automatically stored after login
# All subsequent requests use it automatically
documents = client.documents.list()
```

### Refresh Access Token

**Endpoint:** `POST /v3/users/refresh_access_token`

**Python:**
```python
new_token = client.users.refresh_access_token("YOUR_REFRESH_TOKEN")
```

### Get Current User

**Endpoint:** `GET /v3/users/me`

**curl:**
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:7272/v3/users/me
```

**Python:**
```python
user_info = client.users.me()
```

---

## Document Management

### Ingest Document from File

**Endpoint:** `POST /v3/ingest_files`

**curl:**
```bash
curl -X POST http://localhost:7272/v3/ingest_files \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@document.pdf" \
  -F "metadata={\"category\":\"research\",\"year\":2024}"
```

**Python:**
```python
# Ingest from file path
response = client.documents.create(
    file_path="/path/to/document.pdf",
    metadata={
        "category": "research",
        "year": 2024,
        "author": "John Doe"
    },
    ingestion_mode="hi-res"  # or "fast"
)

# Response includes document_id
print(response["document_id"])
```

### Ingest Raw Text

**Python:**
```python
response = client.documents.create(
    raw_text="This is my document content. It can be multiple paragraphs.",
    metadata={"source": "manual_entry"}
)
```

### Ingest Pre-Chunked Text

**Python:**
```python
response = client.documents.create(
    chunks=[
        "First chunk of content",
        "Second chunk of content",
        "Third chunk of content"
    ],
    metadata={"source": "api"}
)
```

### Ingestion Modes

- `fast` - Quick processing, lower quality (basic text extraction)
- `hi-res` - High quality, slower (uses Unstructured with vision models for tables, images)

**Example:**
```python
# Fast mode for simple documents
client.documents.create(
    file_path="simple.txt",
    ingestion_mode="fast"
)

# Hi-res mode for complex PDFs with tables/images
client.documents.create(
    file_path="complex_report.pdf",
    ingestion_mode="hi-res"
)
```

### List Documents

**Endpoint:** `GET /v3/documents`

**curl:**
```bash
curl -X GET http://localhost:7272/v3/documents \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
# List all documents
documents = client.documents.list()

# List with pagination
documents = client.documents.list(offset=0, limit=10)

# List with filters
documents = client.documents.list(
    filter={"category": {"$eq": "research"}}
)
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid-here",
      "title": "Document Title",
      "metadata": {
        "category": "research",
        "year": 2024
      },
      "created_at": "2024-12-19T10:00:00Z",
      "updated_at": "2024-12-19T10:00:00Z"
    }
  ],
  "total_entries": 42
}
```

### Get Document

**Endpoint:** `GET /v3/documents/{document_id}`

**curl:**
```bash
curl -X GET http://localhost:7272/v3/documents/{document_id} \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
document = client.documents.retrieve(document_id="uuid-here")
```

### Update Document Metadata

**Endpoint:** `PATCH /v3/documents/{document_id}`

**curl:**
```bash
curl -X PATCH http://localhost:7272/v3/documents/{document_id} \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"category": "updated_category"}}'
```

**Python:**
```python
response = client.documents.update(
    document_id="uuid-here",
    metadata={"category": "updated_category"}
)
```

### Delete Document

**Endpoint:** `DELETE /v3/documents/{document_id}`

**curl:**
```bash
curl -X DELETE http://localhost:7272/v3/documents/{document_id} \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
response = client.documents.delete(document_id="uuid-here")
```

---

## Search & RAG

### Search Documents

**Endpoint:** `POST /v3/search`

**curl:**
```bash
curl -X POST http://localhost:7272/v3/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "query": "What is machine learning?",
    "search_mode": "advanced",
    "search_settings": {
      "limit": 10,
      "use_hybrid_search": true
    }
  }'
```

**Python:**
```python
# Basic search (semantic only)
results = client.retrieval.search(
    query="What is machine learning?",
    search_mode="basic"
)

# Advanced search (hybrid: semantic + full-text)
results = client.retrieval.search(
    query="What is machine learning?",
    search_mode="advanced"
)

# Custom search with filters
results = client.retrieval.search(
    query="deep learning",
    search_mode="custom",
    search_settings={
        "use_semantic_search": True,
        "use_fulltext_search": True,
        "use_hybrid_search": True,
        "hybrid_settings": {
            "semantic_weight": 5.0,
            "full_text_weight": 1.0,
            "rrf_k": 50
        },
        "limit": 10,
        "filters": {
            "category": {"$eq": "research"},
            "year": {"$gte": 2023}
        }
    }
)
```

**Search Modes:**
- `basic` - Semantic search only (vector similarity)
- `advanced` - Hybrid search (semantic + full-text with smart defaults)
- `custom` - Full control via `search_settings`

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "uuid-chunk-1",
      "document_id": "uuid-doc-1",
      "text": "Machine learning is a subset of AI...",
      "metadata": {
        "title": "ML Introduction",
        "page": 5
      },
      "score": 0.87
    }
  ]
}
```

### RAG (Retrieval-Augmented Generation)

**Endpoint:** `POST /v3/rag`

**curl:**
```bash
curl -X POST http://localhost:7272/v3/rag \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "query": "Explain deep learning",
    "rag_generation_config": {
      "model": "openai/gpt-4o-mini",
      "temperature": 0.7,
      "max_tokens": 500,
      "stream": false
    },
    "search_settings": {
      "limit": 5
    }
  }'
```

**Python:**
```python
# Basic RAG with default settings
response = client.retrieval.rag(
    query="What is machine learning?"
)

# RAG with custom LLM settings
response = client.retrieval.rag(
    query="Explain deep learning in simple terms",
    rag_generation_config={
        "model": "anthropic/claude-3-haiku-20240307",
        "temperature": 0.3,
        "max_tokens_to_sample": 500
    },
    search_settings={"limit": 5}
)

# RAG with streaming
response = client.retrieval.rag(
    query="What is quantum computing?",
    rag_generation_config={
        "stream": True
    }
)

# For streaming responses
for chunk in response:
    print(chunk, end="", flush=True)
```

**Available Models:**
- `openai/gpt-4o` - Best quality
- `openai/gpt-4o-mini` - Fast and cost-effective
- `anthropic/claude-3-opus-20240229` - High quality
- `anthropic/claude-3-haiku-20240307` - Fast and cheap

**Response (non-streaming):**
```json
{
  "completion": "Machine learning is a branch of artificial intelligence...",
  "search_results": [
    {
      "chunk_id": "uuid",
      "text": "...",
      "score": 0.89
    }
  ]
}
```

### Agentic RAG

**Endpoint:** `POST /v3/agent`

**Python:**
```python
# Agentic RAG with file knowledge tools
response = client.retrieval.agent(
    message={
        "role": "user",
        "content": "Research AI safety developments in the last year"
    },
    rag_tools=["search_file_knowledge", "web_search", "web_scrape"],
    mode="rag"
)

# Research mode with reasoning tools
response = client.retrieval.agent(
    message={
        "role": "user",
        "content": "Analyze this algorithm's time complexity"
    },
    research_tools=["reasoning", "python_executor"],
    mode="research"
)
```

**Available RAG Tools:**
- `search_file_knowledge` - Search ingested documents
- `get_file_content` - Retrieve full document
- `web_search` - Search the web
- `web_scrape` - Scrape websites

**Available Research Tools:**
- `reasoning` - Chain-of-thought reasoning
- `python_executor` - Execute Python code

---

## Knowledge Graphs

### Pull/Extract Graph Data

**Endpoint:** `POST /v3/collections/{collection_id}/graphs/pull`

**curl:**
```bash
curl -X POST http://localhost:7272/v3/collections/{collection_id}/graphs/pull \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
# Extract entities and relationships from collection
response = client.graphs.pull(collection_id="uuid-here")
```

### List Entities

**Endpoint:** `GET /v3/collections/{collection_id}/graphs/entities`

**curl:**
```bash
curl -X GET http://localhost:7272/v3/collections/{collection_id}/graphs/entities \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
# Get all entities
entities = client.graphs.list_entities(collection_id="uuid-here")

# Get entities with filters
entities = client.graphs.list_entities(
    collection_id="uuid-here",
    entity_type="Person",
    limit=10
)
```

**Response:**
```json
{
  "entities": [
    {
      "id": "entity-uuid-1",
      "name": "John Doe",
      "type": "Person",
      "description": "AI researcher at OpenAI",
      "metadata": {}
    }
  ]
}
```

### List Relationships

**Endpoint:** `GET /v3/collections/{collection_id}/graphs/relationships`

**curl:**
```bash
curl -X GET http://localhost:7272/v3/collections/{collection_id}/graphs/relationships \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
# Get all relationships
relationships = client.graphs.list_relationships(collection_id="uuid-here")

# Get relationships with filters
relationships = client.graphs.list_relationships(
    collection_id="uuid-here",
    relation_type="works_for"
)
```

**Response:**
```json
{
  "relationships": [
    {
      "id": "rel-uuid-1",
      "source_entity": "entity-uuid-1",
      "target_entity": "entity-uuid-2",
      "relation_type": "works_for",
      "description": "John Doe works for OpenAI"
    }
  ]
}
```

### Build Graph Communities

**Python:**
```python
# Build communities (clustering of entities)
response = client.graphs.build(
    collection_id="uuid-here",
    settings={
        "algorithm": "leiden",
        "resolution": 1.0
    }
)
```

### List Communities

**Python:**
```python
communities = client.graphs.list_communities(collection_id="uuid-here")
```

**Response:**
```json
{
  "communities": [
    {
      "id": "community-uuid-1",
      "name": "AI Research Team",
      "entities": ["entity-uuid-1", "entity-uuid-2"],
      "description": "Group of AI researchers working on safety"
    }
  ]
}
```

### RAG with Knowledge Graph Enhancement

**Python:**
```python
# Standard RAG
response = client.retrieval.rag(
    query="Who works on AI safety?"
)

# Graph-enhanced RAG (better for entity/relationship questions)
response = client.retrieval.rag(
    query="Who works on AI safety and what are they researching?",
    graph_settings={
        "enabled": True,
        "kg_search_type": "local"  # or "global"
    }
)
```

**Knowledge Graph Search Types:**
- `local` - Search within specific communities
- `global` - Search across entire graph

---

## Collections

### Create Collection

**Endpoint:** `POST /v3/collections`

**curl:**
```bash
curl -X POST http://localhost:7272/v3/collections \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "My Collection",
    "description": "Collection of research papers"
  }'
```

**Python:**
```python
collection = client.collections.create(
    name="Research Papers",
    description="Collection of ML research papers"
)
```

### List Collections

**Endpoint:** `GET /v3/collections`

**curl:**
```bash
curl -X GET http://localhost:7272/v3/collections \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
collections = client.collections.list()
```

### Get Collection

**Endpoint:** `GET /v3/collections/{collection_id}`

**Python:**
```python
collection = client.collections.retrieve(collection_id="uuid-here")
```

### Update Collection

**Endpoint:** `PATCH /v3/collections/{collection_id}`

**Python:**
```python
response = client.collections.update(
    collection_id="uuid-here",
    name="Updated Name",
    description="Updated description"
)
```

### Delete Collection

**Endpoint:** `DELETE /v3/collections/{collection_id}`

**curl:**
```bash
curl -X DELETE http://localhost:7272/v3/collections/{collection_id} \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
response = client.collections.delete(collection_id="uuid-here")
```

### Add Document to Collection

**Endpoint:** `POST /v3/collections/{collection_id}/documents`

**curl:**
```bash
curl -X POST http://localhost:7272/v3/collections/{collection_id}/documents \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@document.pdf"
```

**Python:**
```python
# Add existing document
response = client.collections.add_document(
    collection_id="collection-uuid",
    document_id="document-uuid"
)

# Or ingest directly to collection
response = client.documents.create(
    file_path="document.pdf",
    collection_ids=["collection-uuid"]
)
```

### List Collection Documents

**Endpoint:** `GET /v3/collections/{collection_id}/documents`

**Python:**
```python
documents = client.collections.list_documents(collection_id="uuid-here")
```

### Remove Document from Collection

**Endpoint:** `DELETE /v3/collections/{collection_id}/documents/{document_id}`

**Python:**
```python
response = client.collections.remove_document(
    collection_id="collection-uuid",
    document_id="document-uuid"
)
```

---

## System

### Health Check

**Endpoint:** `GET /v3/health`

**curl:**
```bash
curl http://localhost:7272/v3/health
```

**Python:**
```python
health = client.system.health()
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "embedding": "ok",
    "completion": "ok"
  },
  "timestamp": "2024-12-19T10:00:00Z"
}
```

### System Settings

**Endpoint:** `GET /v3/system/settings`

**curl:**
```bash
curl -X GET http://localhost:7272/v3/system/settings \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
settings = client.system.settings()
```

### System Logs

**Endpoint:** `GET /v3/system/logs`

**curl:**
```bash
# Get last 10 logs
curl -X GET "http://localhost:7272/v3/system/logs?limit=10" \
  -H "Authorization: Bearer TOKEN"

# Get logs with filters
curl -X GET "http://localhost:7272/v3/system/logs?log_type_filter=error&limit=20" \
  -H "Authorization: Bearer TOKEN"
```

**Python:**
```python
# Get recent logs
logs = client.system.logs(limit=10)

# Get error logs only
logs = client.system.logs(
    log_type_filter="error",
    limit=20
)
```

### System Statistics

**Endpoint:** `GET /v3/system/statistics`

**Python:**
```python
stats = client.system.statistics()
```

**Response:**
```json
{
  "documents_count": 150,
  "chunks_count": 5420,
  "users_count": 25,
  "collections_count": 10
}
```

---

## Best Practices

### 1. Always Use Authentication in Production

```toml
[auth]
require_authentication = true
require_email_verification = true
```

### 2. Use Hybrid Search for Best Results

```python
# Recommended: Advanced mode (hybrid search)
results = client.retrieval.search(
    query="machine learning",
    search_mode="advanced"
)
```

### 3. Enable Knowledge Graphs for Complex Documents

```python
# First pull graph data
client.graphs.pull(collection_id)

# Then use graph-enhanced RAG
response = client.retrieval.rag(
    query="Explain relationships between concepts",
    graph_settings={"enabled": True}
)
```

### 4. Set Reasonable Limits to Control Costs

```python
# Limit search results
results = client.retrieval.search(
    query="...",
    search_settings={"limit": 5}  # Not 100!
)

# Use cheaper models for simple tasks
response = client.retrieval.rag(
    query="simple question",
    rag_generation_config={
        "model": "openai/gpt-4o-mini"  # Cheaper than gpt-4o
    }
)
```

### 5. Monitor Logs for Issues

```python
# Check recent errors
logs = client.system.logs(
    log_type_filter="error",
    limit=50
)
```

### 6. Use Collections to Organize Documents

```python
# Create collection for specific topic
collection = client.collections.create(name="AI Safety Papers")

# Ingest documents to collection
client.documents.create(
    file_path="paper.pdf",
    collection_ids=[collection["id"]]
)

# Search within collection
results = client.retrieval.search(
    query="safety alignment",
    search_settings={
        "filters": {
            "collection_ids": [collection["id"]]
        }
    }
)
```

### 7. Stream RAG Responses for Better UX

```python
response = client.retrieval.rag(
    query="Explain this concept in detail",
    rag_generation_config={"stream": True}
)

for chunk in response:
    print(chunk, end="", flush=True)
```

### 8. Use Metadata for Filtering

```python
# Add metadata during ingestion
client.documents.create(
    file_path="paper.pdf",
    metadata={
        "category": "research",
        "year": 2024,
        "topic": "deep_learning"
    }
)

# Filter by metadata during search
results = client.retrieval.search(
    query="neural networks",
    search_settings={
        "filters": {
            "category": {"$eq": "research"},
            "year": {"$gte": 2023}
        }
    }
)
```

---

## Common Metadata Filters

| Operator | Description | Example |
|----------|-------------|---------|
| `$eq` | Equal | `{"year": {"$eq": 2024}}` |
| `$ne` | Not equal | `{"status": {"$ne": "draft"}}` |
| `$gt` | Greater than | `{"score": {"$gt": 0.8}}` |
| `$gte` | Greater or equal | `{"year": {"$gte": 2023}}` |
| `$lt` | Less than | `{"price": {"$lt": 100}}` |
| `$lte` | Less or equal | `{"price": {"$lte": 50}}` |
| `$in` | In array | `{"category": {"$in": ["research", "blog"]}}` |
| `$nin` | Not in array | `{"status": {"$nin": ["draft", "archived"]}}` |

---

## Rate Limits

Configure in r2r.toml:

```toml
[database.limits]
global_per_min = 60      # Global requests per minute
route_per_min = 20       # Per-route requests per minute
monthly_limit = 10000    # Monthly request limit

# Per-route overrides
[database.route_limits]
  "/v3/rag" = { route_per_min = 10 }
  "/v3/ingest_files" = { route_per_min = 5 }
```

---

## Error Codes

| Status Code | Meaning | Example |
|-------------|---------|---------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid JSON, missing required fields |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Document/collection not found |
| 413 | Payload Too Large | File exceeds upload size limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error (check logs) |
| 503 | Service Unavailable | Service temporarily down |
