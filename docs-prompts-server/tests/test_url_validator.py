"""
Unit tests for URLValidator class
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from url_validator import URLValidator


class TestURLValidator:
    """Test cases for URLValidator functionality"""

    def test_validate_basic_github_url(self):
        """Test validation of basic GitHub repository URL"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/microsoft/vscode"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref is None

    def test_validate_github_url_with_git_extension(self):
        """Test validation of GitHub URL with .git extension"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/microsoft/vscode.git"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref is None

    def test_validate_github_url_with_tree_ref(self):
        """Test validation of GitHub URL with tree/branch reference"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/microsoft/vscode/tree/main"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref == "main"

    def test_validate_github_url_with_blob_ref(self):
        """Test validation of GitHub URL with blob/branch reference"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/microsoft/vscode/blob/main/README.md"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref == "main"

    def test_validate_ssh_github_url(self):
        """Test validation of SSH GitHub URL"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "git@github.com:microsoft/vscode.git"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref is None

    def test_validate_http_github_url(self):
        """Test validation of HTTP GitHub URL"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "http://github.com/microsoft/vscode"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref is None

    def test_invalid_empty_url(self):
        """Test that empty URL raises ValueError"""
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            URLValidator.validate_and_parse_github_url("")

    def test_invalid_none_url(self):
        """Test that None URL raises ValueError"""
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            URLValidator.validate_and_parse_github_url(None)

    def test_invalid_non_string_url(self):
        """Test that non-string URL raises ValueError"""
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            URLValidator.validate_and_parse_github_url(123)

    def test_invalid_domain(self):
        """Test that non-GitHub domain raises ValueError"""
        with pytest.raises(ValueError,
                          match="Domain 'example.com' is not allowed"):
            URLValidator.validate_and_parse_github_url(
                "https://example.com/repo"
            )

    def test_invalid_github_url_format(self):
        """Test that malformed GitHub URL raises ValueError"""
        with pytest.raises(ValueError,
                          match="URL is not a valid GitHub repository URL"):
            URLValidator.validate_and_parse_github_url("https://github.com")

    def test_invalid_github_url_no_repo(self):
        """Test that GitHub URL without repo name raises ValueError"""
        with pytest.raises(ValueError, match="URL is not a valid GitHub repository URL"):
            URLValidator.validate_and_parse_github_url("https://github.com/microsoft")

    def test_invalid_url_format(self):
        """Test that completely invalid URL format raises ValueError"""
        with pytest.raises(ValueError, match="Domain '' is not allowed"):
            URLValidator.validate_and_parse_github_url("not-a-url-at-all")

    def test_is_github_url_valid(self):
        """Test is_github_url returns True for valid GitHub URLs"""
        assert URLValidator.is_github_url("https://github.com/microsoft/vscode") is True
        assert URLValidator.is_github_url("https://github.com/microsoft/vscode/tree/main") is True
        assert URLValidator.is_github_url("git@github.com:microsoft/vscode.git") is True

    def test_is_github_url_invalid(self):
        """Test is_github_url returns False for invalid URLs"""
        assert URLValidator.is_github_url("") is False
        assert URLValidator.is_github_url("https://example.com/repo") is False
        assert URLValidator.is_github_url("https://github.com") is False
        assert URLValidator.is_github_url("not-a-url") is False

    def test_extract_repo_info_valid(self):
        """Test extract_repo_info works for valid URLs"""
        owner, repo, ref = URLValidator.extract_repo_info("https://github.com/microsoft/vscode")
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref is None

    def test_extract_repo_info_invalid(self):
        """Test extract_repo_info raises ValueError for invalid URLs"""
        with pytest.raises(ValueError):
            URLValidator.extract_repo_info("https://example.com/repo")

    def test_case_sensitivity(self):
        """Test that URL validation is case-sensitive for domain"""
        # Domain should be lowercase
        with pytest.raises(ValueError):
            URLValidator.validate_and_parse_github_url("https://GITHUB.COM/microsoft/vscode")

    def test_special_characters_in_repo_name(self):
        """Test repository names with allowed special characters"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/microsoft/vscode-web"
        )
        assert owner == "microsoft"
        assert repo == "vscode-web"
        assert ref is None

    def test_numeric_owner_repo(self):
        """Test repository with numeric characters"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/user123/repo456"
        )
        assert owner == "user123"
        assert repo == "repo456"
        assert ref is None

    def test_url_with_query_params(self):
        """Test URL with query parameters (should still work for basic repo URL)"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/microsoft/vscode?tab=readme"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref is None

    def test_tree_url_with_path(self):
        """Test tree URL with additional path components"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/microsoft/vscode/tree/main/src"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref == "main"

    def test_blob_url_with_path(self):
        """Test blob URL with file path"""
        owner, repo, ref = URLValidator.validate_and_parse_github_url(
            "https://github.com/microsoft/vscode/blob/main/package.json"
        )
        assert owner == "microsoft"
        assert repo == "vscode"
        assert ref == "main"
