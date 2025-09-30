"""
URL validation and GitHub URL parsing utilities
"""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse


class URLValidator:
    """Validates URLs and parses GitHub repository information"""

    # GitHub URL patterns
    GITHUB_URL_PATTERNS = [
        r'^https?://github\.com/([^/]+)/([^/?]+)(?:\.git)?(?:\?.*)?$',
        r'^https?://github\.com/([^/]+)/([^/]+)/tree/([^/?]+)'
        r'(?:/.+)?(?:\?.*)?$',
        r'^https?://github\.com/([^/]+)/([^/]+)/blob/([^/?]+)'
        r'(?:/.+)?(?:\?.*)?$',
        r'^git@github\.com:([^/]+)/([^/]+)(?:\.git)?$',
    ]

    # Allowed domains for security
    ALLOWED_DOMAINS = {'github.com'}

    @staticmethod
    def _parse_ssh_url(url: str) -> Tuple[str, str, Optional[str]]:
        """
        Parse SSH GitHub URL format: git@github.com:owner/repo.git

        Args:
            url: SSH URL to parse

        Returns:
            Tuple of (owner, repo_name, ref) where ref is None for SSH URLs

        Raises:
            ValueError: If URL format is invalid
        """
        # SSH URL pattern: git@github.com:owner/repo(.git)?
        pattern = r'^git@github\.com:([^/]+)/([^/]+)(?:\.git)?$'
        match = re.match(pattern, url)
        if not match:
            raise ValueError(
                "Invalid SSH GitHub URL format. "
                "Expected: git@github.com:owner/repo(.git)?"
            )

        owner, repo = match.groups()
        # Strip .git extension if present
        repo = repo.rstrip('.git')
        return owner, repo, None

    @staticmethod
    def validate_and_parse_github_url(
        url: str
    ) -> Tuple[str, str, Optional[str]]:
        """
        Validate a URL and extract GitHub repository information.

        Args:
            url: The URL to validate and parse

        Returns:
            Tuple of (owner, repo_name, ref) where ref is optional

        Raises:
            ValueError: If URL is invalid or not a supported GitHub URL
        """
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")

        # Handle SSH URLs separately since urlparse doesn't work for them
        if url.startswith('git@github.com:'):
            return URLValidator._parse_ssh_url(url)

        # Parse the URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}") from e

        if parsed.netloc not in URLValidator.ALLOWED_DOMAINS:
            raise ValueError(
                f"Domain '{parsed.netloc}' is not allowed. "
                "Only GitHub URLs are supported."
            )

        # Try to match against GitHub URL patterns
        for pattern in URLValidator.GITHUB_URL_PATTERNS:
            match = re.match(pattern, url)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    # Basic repo URL: https://github.com/owner/repo
                    owner, repo = groups
                    # Strip .git extension if present
                    repo = repo.rstrip('.git')
                    return owner, repo, None
                elif len(groups) == 3:
                    # URL with ref: https://github.com/owner/repo/tree/branch
                    # or blob/branch
                    owner, repo, ref = groups
                    return owner, repo, ref

        raise ValueError(
            "URL is not a valid GitHub repository URL. "
            "Supported formats: https://github.com/owner/repo, "
            "https://github.com/owner/repo/tree/branch, "
            "https://github.com/owner/repo/blob/branch, "
            "git@github.com:owner/repo.git"
        )

    @staticmethod
    def is_github_url(url: str) -> bool:
        """
        Check if a URL is a valid GitHub URL without raising exceptions.

        Args:
            url: The URL to check

        Returns:
            True if the URL is a valid GitHub URL, False otherwise
        """
        try:
            URLValidator.validate_and_parse_github_url(url)
            return True
        except ValueError:
            return False

    @staticmethod
    def extract_repo_info(url: str) -> Tuple[str, str, Optional[str]]:
        """
        Extract repository information from a GitHub URL.

        Args:
            url: The GitHub URL to parse

        Returns:
            Tuple of (owner, repo_name, ref) where ref is optional

        Raises:
            ValueError: If URL parsing fails
        """
        return URLValidator.validate_and_parse_github_url(url)

