"""Pytest configuration for content organization tests."""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """Get path to test data directory."""
    return os.path.join(os.path.dirname(__file__), 'data')

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def course_content_dir(test_data_dir):
    """Get path to course content test data."""
    return os.path.join(test_data_dir, 'course_content')

@pytest.fixture
def file_organization_dir(test_data_dir):
    """Get path to file organization test data."""
    return os.path.join(test_data_dir, 'file_organization')

@pytest.fixture
def cross_references_dir(test_data_dir):
    """Get path to cross-references test data."""
    return os.path.join(test_data_dir, 'cross_references')