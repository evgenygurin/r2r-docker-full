#!/usr/bin/env python3
"""
R2R Repository Loader - Production-ready code repository ingestion

Load any Git repository into R2R with full metadata extraction, KG generation,
and quality optimization for code search and RAG.

Usage:
    python repo_loader.py https://github.com/user/repo
    python repo_loader.py https://github.com/user/repo --collection my-codebase
    python repo_loader.py https://github.com/user/repo --update --extract-kg
"""
import argparse
import sys
import time
import logging
import uuid
import hashlib
from pathlib import Path
from typing import Optional

from config import (
    R2R_EMAIL,
    R2R_PASSWORD,
    UPLOAD_DELAY_MS,
    INGESTION_CONFIG,
)
from r2r_client import R2RClient
from git_manager import GitManager
from file_filter import FileFilter
from metadata_extractor import MetadataExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_document_id(repo_url: str, file_path: str) -> str:
    """
    Generate deterministic UUID for document based on repo URL and file path.

    This ensures:
    - Same file in same repo always gets same ID (idempotent updates)
    - Different files with same content get different IDs (no conflicts)
    - ID is valid UUID format required by R2R

    Uses UUID5 with DNS namespace + hash of repo_url:file_path
    """
    unique_key = f"{repo_url}:{file_path}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_key))


class RepositoryLoader:
    """
    Main orchestrator для загрузки репозиториев в R2R

    WORKFLOW:
    1. Clone/update repository
    2. Filter code files
    3. Create/get collection
    4. Upload files с metadata
    5. Wait for ingestion
    6. Extract Knowledge Graph (optional)
    7. Report statistics
    """

    def __init__(
        self,
        r2r_client: R2RClient,
        git_manager: GitManager,
    ):
        self.client = r2r_client
        self.git = git_manager

    def load_repository(
        self,
        repo_url: str,
        collection_name: Optional[str] = None,
        branch: Optional[str] = None,
        update_if_exists: bool = False,
        extract_kg: bool = False,
        quality_mode: str = 'high',
        verbose: bool = False,
    ) -> dict:
        """
        Load Git repository into R2R

        Args:
            repo_url: Git repository URL
            collection_name: Target collection name (default: repo name)
            branch: Git branch (default: remote HEAD)
            update_if_exists: Pull latest changes if repo exists locally
            extract_kg: Extract Knowledge Graph after ingestion
            quality_mode: Processing quality ('high', 'fast')
            verbose: Verbose output

        Returns:
            Statistics dict with counts and timings
        """
        start_time = time.time()
        stats = {
            'repo_url': repo_url,
            'files_found': 0,
            'files_uploaded': 0,
            'files_failed': 0,
            'collection_id': None,
            'kg_entities': 0,
            'kg_relationships': 0,
            'duration_seconds': 0,
        }

        # =======================================================================
        # STEP 1: Clone/Update Repository
        # =======================================================================
        logger.info(f"{'='*70}")
        logger.info(f"STEP 1: REPOSITORY MANAGEMENT")
        logger.info(f"{'='*70}")

        if update_if_exists:
            repo_path, was_updated = self.git.clone_or_update(repo_url, branch=branch)
            if was_updated:
                logger.info("✓ Repository updated with latest changes")
        else:
            repo_path = self.git.clone(repo_url, branch=branch)

        repo_name = repo_path.name
        commit_info = self.git.get_commit_info(repo_path)

        logger.info(f"Repository: {repo_name}")
        logger.info(f"Path: {repo_path}")
        logger.info(f"Commit: {commit_info['hash_short']} - {commit_info['message']}")

        # =======================================================================
        # STEP 2: Filter Code Files
        # =======================================================================
        logger.info(f"\n{'='*70}")
        logger.info(f"STEP 2: FILE FILTERING")
        logger.info(f"{'='*70}")

        file_filter = FileFilter(repo_path)
        files = file_filter.filter_files(verbose=verbose)

        stats['files_found'] = len(files)

        if not files:
            logger.warning("No valid code files found in repository!")
            return stats

        # Group by language
        by_language = file_filter.group_by_language(files)
        total_size = file_filter.estimate_total_size(files)

        logger.info(f"Found {len(files)} code files ({total_size / 1024 / 1024:.1f}MB)")
        for lang, lang_files in sorted(by_language.items(), key=lambda x: -len(x[1])):
            logger.info(f"  {lang}: {len(lang_files)} files")

        # =======================================================================
        # STEP 3: Create/Get Collection
        # =======================================================================
        logger.info(f"\n{'='*70}")
        logger.info(f"STEP 3: COLLECTION SETUP")
        logger.info(f"{'='*70}")

        if not collection_name:
            collection_name = f"repo-{repo_name}"

        collection = self.client.create_collection(
            name=collection_name,
            description=f"Code repository: {repo_url}"
        )
        collection_id = collection['id']
        stats['collection_id'] = collection_id

        logger.info(f"Collection: {collection_name} ({collection_id[:8]}...)")

        # =======================================================================
        # STEP 4: Upload Files
        # =======================================================================
        logger.info(f"\n{'='*70}")
        logger.info(f"STEP 4: FILE UPLOAD")
        logger.info(f"{'='*70}")

        metadata_extractor = MetadataExtractor(repo_path)
        document_ids = []
        upload_start = time.time()

        for i, file_path in enumerate(files, 1):
            try:
                # Get relative path for ID generation and logging
                rel_path = file_filter.get_relative_path(file_path)

                # Generate unique document ID based on repo URL + file path
                # This prevents conflicts when multiple files have same content
                doc_id = generate_document_id(repo_url, rel_path)

                # Extract metadata
                language = file_filter.get_file_language(file_path)
                metadata = metadata_extractor.build_metadata(
                    file_path=file_path,
                    language=language,
                    repo_url=repo_url,
                    repo_name=repo_name,
                    commit_info=commit_info,
                )

                # Upload (r2r_client handles filename renaming for unsupported extensions)
                result = self.client.upload_document(
                    file_path=file_path,
                    metadata=metadata,
                    collection_id=collection_id,
                    document_id=doc_id
                )

                document_ids.append(result['document_id'])
                stats['files_uploaded'] += 1

                # Progress
                progress = (i / len(files)) * 100
                logger.info(f"[{progress:5.1f}%] {rel_path} → {result['document_id'][:8]}...")

                # Rate limiting
                time.sleep(UPLOAD_DELAY_MS / 1000)

            except Exception as e:
                stats['files_failed'] += 1
                logger.error(f"Failed to upload {file_path.name}: {e}")

        upload_duration = time.time() - upload_start
        logger.info(f"\n✓ Uploaded {stats['files_uploaded']}/{len(files)} files in {upload_duration:.1f}s")

        if stats['files_failed'] > 0:
            logger.warning(f"⚠ {stats['files_failed']} files failed to upload")

        # =======================================================================
        # STEP 5: Wait for Ingestion
        # =======================================================================
        logger.info(f"\n{'='*70}")
        logger.info(f"STEP 5: INGESTION MONITORING")
        logger.info(f"{'='*70}")

        ingestion_statuses = self.client.wait_for_ingestion(
            document_ids=document_ids,
            timeout=300,
            poll_interval=5
        )

        success_count = sum(1 for s in ingestion_statuses.values() if s == 'success')
        failed_count = sum(1 for s in ingestion_statuses.values() if s == 'failed')

        logger.info(f"✓ Ingestion complete: {success_count} successful, {failed_count} failed")

        # =======================================================================
        # STEP 6: Knowledge Graph Extraction (Optional)
        # =======================================================================
        if extract_kg:
            logger.info(f"\n{'='*70}")
            logger.info(f"STEP 6: KNOWLEDGE GRAPH EXTRACTION")
            logger.info(f"{'='*70}")

            try:
                # Pull KG
                self.client.pull_knowledge_graph(collection_id, force=False)

                # Wait for extraction
                logger.info("Waiting for KG extraction (30s)...")
                time.sleep(30)

                # Get entities and relationships
                entities = self.client.get_graph_entities(collection_id, limit=1000)
                relationships = self.client.get_graph_relationships(collection_id, limit=1000)

                stats['kg_entities'] = len(entities)
                stats['kg_relationships'] = len(relationships)

                logger.info(f"✓ Knowledge Graph: {len(entities)} entities, {len(relationships)} relationships")

                # Sample entities
                if entities and verbose:
                    logger.info("\nSample entities:")
                    for entity in entities[:5]:
                        logger.info(f"  {entity.get('name', 'N/A')} ({entity.get('category', 'N/A')})")

            except Exception as e:
                logger.error(f"Knowledge Graph extraction failed: {e}")

        # =======================================================================
        # SUMMARY
        # =======================================================================
        stats['duration_seconds'] = int(time.time() - start_time)

        logger.info(f"\n{'='*70}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Repository: {repo_name}")
        logger.info(f"Collection: {collection_name} ({collection_id[:8]}...)")
        logger.info(f"Files found: {stats['files_found']}")
        logger.info(f"Files uploaded: {stats['files_uploaded']}")
        logger.info(f"Files failed: {stats['files_failed']}")
        if extract_kg:
            logger.info(f"KG Entities: {stats['kg_entities']}")
            logger.info(f"KG Relationships: {stats['kg_relationships']}")
        logger.info(f"Duration: {stats['duration_seconds']}s")
        logger.info(f"{'='*70}\n")

        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Load Git repository into R2R for code search and RAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load repository with default settings
  python repo_loader.py https://github.com/user/repo

  # Load into specific collection
  python repo_loader.py https://github.com/user/repo --collection my-codebase

  # Update existing repo and extract Knowledge Graph
  python repo_loader.py https://github.com/user/repo --update --extract-kg

  # Verbose output
  python repo_loader.py https://github.com/user/repo --verbose
        """
    )

    parser.add_argument(
        'repo_url',
        help='Git repository URL (https:// or git@)'
    )

    parser.add_argument(
        '--collection',
        help='Collection name (default: auto-generated from repo name)'
    )

    parser.add_argument(
        '--branch',
        help='Git branch (default: remote HEAD)'
    )

    parser.add_argument(
        '--update',
        action='store_true',
        help='Update repository if exists locally'
    )

    parser.add_argument(
        '--extract-kg',
        action='store_true',
        help='Extract Knowledge Graph after ingestion'
    )

    parser.add_argument(
        '--quality',
        choices=['high', 'fast'],
        default='high',
        help='Processing quality mode (default: high)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output with detailed logging'
    )

    parser.add_argument(
        '--email',
        default=R2R_EMAIL,
        help=f'R2R account email (default: {R2R_EMAIL})'
    )

    parser.add_argument(
        '--password',
        default=R2R_PASSWORD,
        help='R2R account password (default: from config)'
    )

    args = parser.parse_args()

    # Initialize components
    try:
        logger.info("Initializing R2R Repository Loader...\n")

        client = R2RClient()
        client.authenticate(args.email, args.password)

        git_manager = GitManager()

        loader = RepositoryLoader(client, git_manager)

        # Load repository
        stats = loader.load_repository(
            repo_url=args.repo_url,
            collection_name=args.collection,
            branch=args.branch,
            update_if_exists=args.update,
            extract_kg=args.extract_kg,
            quality_mode=args.quality,
            verbose=args.verbose,
        )

        # Exit code based on success rate
        success_rate = stats['files_uploaded'] / max(stats['files_found'], 1)
        if success_rate >= 0.9:
            sys.exit(0)
        elif success_rate >= 0.5:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # Mostly failed

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
