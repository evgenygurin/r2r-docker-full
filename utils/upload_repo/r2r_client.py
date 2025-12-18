"""
R2R API Client with retry logic and error handling
"""
import requests
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from config import (
    R2R_API_URL,
    API_RETRY_ATTEMPTS,
    API_RETRY_BACKOFF,
    UPLOAD_DELAY_MS,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class R2RClientError(Exception):
    """Base exception for R2R client errors"""
    pass


class R2RClient:
    """
    R2R API client with authentication, collections, documents, and KG operations

    ARCHITECTURE:
    - OAuth2 password flow для auth
    - Retry logic с exponential backoff
    - Rate limiting между uploads
    - Automatic token management
    """

    def __init__(self, api_url: str = R2R_API_URL):
        self.api_url = api_url
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}

    def _retry_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """
        Retry HTTP request с exponential backoff

        RATIONALE: API может временно быть недоступен или rate limited
        """
        for attempt in range(API_RETRY_ATTEMPTS):
            try:
                response = requests.request(method, url, **kwargs)

                # Success codes
                if response.status_code in [200, 201, 202]:
                    return response

                # Rate limit - wait and retry
                if response.status_code == 429:
                    wait_time = (2 ** attempt) * API_RETRY_BACKOFF
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Client errors - don't retry
                if 400 <= response.status_code < 500:
                    logger.error(f"Client error {response.status_code}: {response.text[:200]}")
                    raise R2RClientError(f"HTTP {response.status_code}: {response.text[:200]}")

                # Server errors - retry
                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, retrying...")
                    time.sleep(2 ** attempt)
                    continue

            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{API_RETRY_ATTEMPTS}): {e}")
                if attempt == API_RETRY_ATTEMPTS - 1:
                    raise R2RClientError(f"Request failed after {API_RETRY_ATTEMPTS} attempts: {e}")
                time.sleep(2 ** attempt)

        raise R2RClientError(f"Failed after {API_RETRY_ATTEMPTS} attempts")

    def authenticate(self, email: str, password: str) -> str:
        """
        OAuth2 password flow authentication

        Returns:
            JWT access token
        """
        logger.info(f"Authenticating as {email}...")

        response = self._retry_request(
            'POST',
            f"{self.api_url}/v3/users/login",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={'username': email, 'password': password}
        )

        result = response.json()['results']
        self.token = result['access_token']['token']
        self.headers = {'Authorization': f'Bearer {self.token}'}

        logger.info("✓ Authenticated successfully")
        return self.token

    def health_check(self) -> Dict[str, Any]:
        """Check R2R API health"""
        response = self._retry_request('GET', f"{self.api_url}/v3/health")
        return response.json()['results']

    # =========================================================================
    # COLLECTIONS API
    # =========================================================================

    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections"""
        response = self._retry_request(
            'GET',
            f"{self.api_url}/v3/collections",
            headers=self.headers
        )
        return response.json()['results']

    def get_collection(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get collection by name

        Returns:
            Collection dict or None if not found
        """
        collections = self.list_collections()
        for coll in collections:
            if coll['name'] == name:
                return coll
        return None

    def create_collection(
        self,
        name: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create new collection or return existing one

        IDEMPOTENT: Если коллекция существует, возвращает её
        """
        existing = self.get_collection(name)
        if existing:
            logger.info(f"Collection '{name}' already exists (ID: {existing['id'][:8]}...)")
            return existing

        logger.info(f"Creating collection '{name}'...")
        response = self._retry_request(
            'POST',
            f"{self.api_url}/v3/collections",
            headers=self.headers,
            json={'name': name, 'description': description}
        )

        result = response.json()['results']
        logger.info(f"✓ Created collection {result['id'][:8]}...")
        return result

    def delete_collection(self, collection_id: str) -> None:
        """Delete collection"""
        logger.info(f"Deleting collection {collection_id[:8]}...")
        self._retry_request(
            'DELETE',
            f"{self.api_url}/v3/collections/{collection_id}",
            headers=self.headers
        )
        logger.info("✓ Collection deleted")

    # =========================================================================
    # DOCUMENTS API
    # =========================================================================

    def upload_document(
        self,
        file_path: Path,
        metadata: Dict[str, Any],
        collection_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload document to R2R

        Args:
            file_path: Path to file
            metadata: Document metadata (language, module, etc.)
            collection_id: Target collection (optional)
            document_id: Custom document ID (optional, prevents duplicates)

        Returns:
            Document info with document_id

        CRITICAL: R2R determines DocumentType from file extension
        For .yaml/.toml/.xml files, we rename them to .txt during upload
        (original name preserved in metadata)

        RATE LIMITING: Вызывающий код должен добавлять delay между вызовами
        """
        with open(file_path, 'rb') as f:
            # CRITICAL: R2R determines DocumentType from file extension, ignoring form data
            # For unsupported extensions (.yaml, .toml, .xml), rename to .txt for upload
            original_name = file_path.name
            upload_name = original_name

            # Map unsupported extensions to .txt
            # R2R doesn't accept 'yaml', 'toml', 'xml', 'sh' as valid DocumentType
            unsupported_extensions = {'.yaml', '.yml', '.toml', '.xml', '.sh', '.bash', '.zsh', '.fish'}
            if file_path.suffix in unsupported_extensions:
                # Replace extension with .txt (preserve original in metadata)
                upload_name = file_path.stem + '.txt'
                logger.debug(f"Renaming {original_name} → {upload_name} for upload")

            files = {'file': (upload_name, f)}
            data = {'metadata': json.dumps(metadata)}

            if collection_id:
                data['collection_ids'] = json.dumps([collection_id])

            if document_id:
                data['id'] = document_id

            response = self._retry_request(
                'POST',
                f"{self.api_url}/v3/documents",
                headers=self.headers,
                files=files,
                data=data
            )

        return response.json()['results']

    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieve document metadata"""
        response = self._retry_request(
            'GET',
            f"{self.api_url}/v3/documents/{document_id}",
            headers=self.headers
        )
        return response.json()['results']

    def list_documents_in_collection(
        self,
        collection_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List documents in collection"""
        response = self._retry_request(
            'GET',
            f"{self.api_url}/v3/collections/{collection_id}/documents",
            headers=self.headers,
            params={'limit': limit, 'offset': offset}
        )
        return response.json()['results']

    def extract_document(self, document_id: str) -> Dict[str, Any]:
        """
        Trigger extraction for document

        NOTE: Extraction запускается асинхронно
        """
        response = self._retry_request(
            'POST',
            f"{self.api_url}/v3/documents/{document_id}/extract",
            headers=self.headers,
            json={}
        )
        return response.json()['results']

    def get_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get document chunks"""
        response = self._retry_request(
            'GET',
            f"{self.api_url}/v3/documents/{document_id}/chunks",
            headers=self.headers
        )
        return response.json()['results']

    # =========================================================================
    # KNOWLEDGE GRAPH API
    # =========================================================================

    def pull_knowledge_graph(
        self,
        collection_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Extract Knowledge Graph entities from collection

        Args:
            collection_id: Collection UUID
            force: Force re-pull даже если уже extracted

        Returns:
            Task info
        """
        logger.info(f"Pulling Knowledge Graph for collection {collection_id[:8]}...")

        response = self._retry_request(
            'POST',
            f"{self.api_url}/v3/graphs/{collection_id}/pull",
            headers=self.headers,
            json=force  # Boolean body: true = force re-pull
        )

        result = response.json()['results']
        logger.info(f"✓ Knowledge Graph pull initiated (task: {result.get('task_id', 'N/A')})")
        return result

    def get_graph_entities(
        self,
        collection_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get Knowledge Graph entities"""
        response = self._retry_request(
            'GET',
            f"{self.api_url}/v3/graphs/{collection_id}/entities",
            headers=self.headers,
            params={'limit': limit}
        )
        return response.json()['results']

    def get_graph_relationships(
        self,
        collection_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get Knowledge Graph relationships"""
        response = self._retry_request(
            'GET',
            f"{self.api_url}/v3/graphs/{collection_id}/relationships",
            headers=self.headers,
            params={'limit': limit}
        )
        return response.json()['results']

    # =========================================================================
    # MONITORING
    # =========================================================================

    def wait_for_ingestion(
        self,
        document_ids: List[str],
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, str]:
        """
        Wait for documents to be ingested

        Returns:
            Dict of {document_id: status}
        """
        logger.info(f"Waiting for {len(document_ids)} documents to be ingested...")

        start_time = time.time()
        statuses = {}

        while time.time() - start_time < timeout:
            all_done = True

            for doc_id in document_ids:
                if doc_id in statuses and statuses[doc_id] in ['success', 'failed']:
                    continue

                try:
                    doc = self.get_document(doc_id)
                    status = doc.get('ingestion_status', 'pending')
                    statuses[doc_id] = status

                    if status not in ['success', 'failed']:
                        all_done = False
                except Exception as e:
                    logger.warning(f"Failed to check {doc_id[:8]}: {e}")
                    all_done = False

            if all_done:
                success_count = sum(1 for s in statuses.values() if s == 'success')
                logger.info(f"✓ Ingestion complete: {success_count}/{len(document_ids)} successful")
                return statuses

            time.sleep(poll_interval)

        logger.warning(f"Timeout waiting for ingestion ({timeout}s)")
        return statuses
