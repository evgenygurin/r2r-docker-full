"""
Git repository management: clone, update, pull
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from config import REPOS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitManagerError(Exception):
    """Base exception for Git manager errors"""
    pass


class GitManager:
    """
    Git repository manager with clone/update/pull operations

    ARCHITECTURE:
    - Clone репозитория в REPOS_DIR
    - Update существующего репозитория через git pull
    - Автоматическое определение имени репо из URL
    - Shallow clone для экономии места
    """

    def __init__(self, repos_dir: Path = REPOS_DIR):
        self.repos_dir = repos_dir
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def _run_git_command(
        self,
        args: list,
        cwd: Optional[Path] = None,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run git command с error handling

        Args:
            args: Git command arguments (e.g., ['clone', 'url'])
            cwd: Working directory
            check: Raise exception on non-zero exit code
        """
        cmd = ['git'] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check
            )
            return result

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(cmd)}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            raise GitManagerError(f"Git command failed: {e.stderr}")

    def _extract_repo_name(self, repo_url: str) -> str:
        """
        Extract repository name from URL

        Examples:
            https://github.com/user/repo.git -> repo
            https://github.com/user/repo -> repo
            git@github.com:user/repo.git -> repo
        """
        # Parse URL
        if repo_url.startswith('git@'):
            # SSH format: git@github.com:user/repo.git
            path = repo_url.split(':')[1]
        else:
            # HTTP(S) format
            parsed = urlparse(repo_url)
            path = parsed.path

        # Remove leading slash and .git extension
        repo_name = path.strip('/').replace('.git', '')

        # Get last component (repo name)
        if '/' in repo_name:
            repo_name = repo_name.split('/')[-1]

        return repo_name

    def get_repo_path(self, repo_url: str) -> Path:
        """Get local path for repository"""
        repo_name = self._extract_repo_name(repo_url)
        return self.repos_dir / repo_name

    def clone(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        depth: Optional[int] = 1,
        force: bool = False
    ) -> Path:
        """
        Clone repository

        Args:
            repo_url: Git repository URL
            branch: Specific branch to clone (default: remote HEAD)
            depth: Shallow clone depth (1 = only latest commit)
            force: Force re-clone if exists

        Returns:
            Path to cloned repository

        SHALLOW CLONE: depth=1 экономит disk space и time
        """
        repo_path = self.get_repo_path(repo_url)

        # Check if already cloned
        if repo_path.exists():
            if force:
                logger.info(f"Force re-clone: removing {repo_path}")
                import shutil
                shutil.rmtree(repo_path)
            else:
                logger.info(f"Repository already exists at {repo_path}")
                return repo_path

        # Build clone command
        logger.info(f"Cloning {repo_url}...")
        clone_args = ['clone']

        if depth:
            clone_args.extend(['--depth', str(depth)])

        if branch:
            clone_args.extend(['--branch', branch])

        clone_args.extend([repo_url, str(repo_path)])

        # Clone
        self._run_git_command(clone_args)

        logger.info(f"✓ Cloned to {repo_path}")
        return repo_path

    def pull(self, repo_path: Path) -> bool:
        """
        Pull latest changes from remote

        Returns:
            True if updated, False if already up-to-date
        """
        if not (repo_path / '.git').exists():
            raise GitManagerError(f"Not a git repository: {repo_path}")

        logger.info(f"Pulling latest changes for {repo_path.name}...")

        result = self._run_git_command(['pull'], cwd=repo_path, check=False)

        if result.returncode == 0:
            if 'Already up to date' in result.stdout:
                logger.info("✓ Already up-to-date")
                return False
            else:
                logger.info("✓ Updated successfully")
                return True
        else:
            logger.warning(f"Pull failed: {result.stderr}")
            return False

    def get_commit_info(self, repo_path: Path) -> dict:
        """
        Get current commit information

        Returns:
            Dict with commit hash, author, date, message
        """
        if not (repo_path / '.git').exists():
            raise GitManagerError(f"Not a git repository: {repo_path}")

        # Get commit hash
        hash_result = self._run_git_command(
            ['rev-parse', 'HEAD'],
            cwd=repo_path
        )
        commit_hash = hash_result.stdout.strip()

        # Get commit message
        msg_result = self._run_git_command(
            ['log', '-1', '--pretty=%s'],
            cwd=repo_path
        )
        commit_message = msg_result.stdout.strip()

        # Get author and date
        info_result = self._run_git_command(
            ['log', '-1', '--pretty=%an|%ae|%ai'],
            cwd=repo_path
        )
        author_name, author_email, author_date = info_result.stdout.strip().split('|')

        return {
            'hash': commit_hash,
            'hash_short': commit_hash[:7],
            'message': commit_message,
            'author_name': author_name,
            'author_email': author_email,
            'date': author_date,
        }

    def get_remote_url(self, repo_path: Path) -> str:
        """Get remote origin URL"""
        if not (repo_path / '.git').exists():
            raise GitManagerError(f"Not a git repository: {repo_path}")

        result = self._run_git_command(
            ['remote', 'get-url', 'origin'],
            cwd=repo_path
        )
        return result.stdout.strip()

    def clone_or_update(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        depth: Optional[int] = 1
    ) -> tuple[Path, bool]:
        """
        Clone repository if not exists, otherwise pull updates

        Returns:
            Tuple of (repo_path, was_updated)
        """
        repo_path = self.get_repo_path(repo_url)

        if repo_path.exists():
            # Repository exists - pull updates
            was_updated = self.pull(repo_path)
            return repo_path, was_updated
        else:
            # Clone new repository
            repo_path = self.clone(repo_url, branch=branch, depth=depth)
            return repo_path, True  # Newly cloned = считается updated
