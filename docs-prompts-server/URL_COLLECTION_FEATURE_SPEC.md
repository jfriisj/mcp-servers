# URL/GitHub Repository Collection Feature Spec

## Overview

This specification outlines the addition of URL-based data collection capabilities to the docs-prompts-server, enabling agents to easily access and search documentation and code from remote GitHub repositories and other URL sources.

## Current Architecture

The docs-prompts-server currently:
- Indexes local files using configurable glob patterns (`documentation_paths`)
- Stores documents in SQLite with full-text search capabilities
- Provides MCP tools for document search, code reuse analysis, and prompt management
- Uses `DocumentInfo` dataclass for document representation

## Feature Requirements

### Core Functionality
- Accept URLs (initially focusing on GitHub repository URLs)
- Download/clone repositories to temporary storage
- Process and index all repository files into the existing database
- Make remote content searchable alongside local content
- Provide clear attribution of content source (local vs remote)

### Supported URL Types
- GitHub repository URLs: `https://github.com/owner/repo`
- GitHub with branch/commit: `https://github.com/owner/repo/tree/branch` or `https://github.com/owner/repo/commit/sha`
- Future: Generic git URLs, direct file URLs, documentation sites

## Implementation Components

### 1. Data Model Extensions

#### Extended DocumentInfo
```python
@dataclass
class DocumentInfo:
    # Existing fields...
    source_url: Optional[str] = None  # URL where content originated
    repo_name: Optional[str] = None   # Repository name (e.g., "owner/repo")
    repo_ref: Optional[str] = None    # Branch, tag, or commit
    download_timestamp: Optional[float] = None  # When content was collected
    is_remote: bool = False           # Distinguish local vs remote content
```

#### Database Schema Updates
Add columns to `documents` table:
- `source_url` TEXT
- `repo_name` TEXT
- `repo_ref` TEXT
- `download_timestamp` REAL
- `is_remote` INTEGER (boolean)

### 2. Repository Collector Module

#### New Class: RepoCollector
```python
class RepoCollector:
    def __init__(self, config: Dict[str, Any], temp_dir: Path):
        self.config = config
        self.temp_dir = temp_dir

    async def collect_from_url(self, url: str, ref: Optional[str] = None) -> RepoCollectionResult:
        """Main entry point for URL collection"""
        # Validate URL
        # Download/clone repository
        # Process files
        # Return results
```

#### URL Validation and Parsing
- Validate GitHub URLs using regex patterns
- Extract owner, repo, and ref information
- Support various GitHub URL formats
- Future: Generic git URL parsing

#### Download Strategies
- **Git Clone**: Full repository clone for complete access
- **Git Archive**: Download specific refs as tarballs (lighter)
- **Shallow Clone**: `--depth=1` for performance
- Configurable timeout and size limits

### 3. MCP Tool Interface

#### New Tool: `collect_from_url`
```yaml
collect_from_url:
  name: "collect_from_url"
  description: "Download and index content from URLs (GitHub repos, etc.)"
  inputSchema:
    type: "object"
    properties:
      url:
        type: "string"
        description: "URL to collect content from"
      ref:
        type: "string"
        description: "Branch, tag, or commit to collect (optional)"
        default: "main"
      include_patterns:
        type: "array"
        items:
          type: "string"
        description: "File patterns to include (optional)"
      exclude_patterns:
        type: "array"
        items:
          type: "string"
        description: "File patterns to exclude (optional)"
      max_depth:
        type: "integer"
        description: "Maximum directory depth to index"
        default: 10
    required: ["url"]
```

#### Tool Response Format
```json
{
  "status": "success|error",
  "message": "Collection completed successfully",
  "repo_info": {
    "name": "owner/repo",
    "url": "https://github.com/owner/repo",
    "ref": "main",
    "files_processed": 150,
    "files_indexed": 145
  },
  "errors": []
}
```

### 4. Integration Points

#### DocumentIndexer Extensions
- Add `index_remote_repository()` method
- Integrate with existing `DocumentProcessor`
- Handle remote file path mapping
- Update progress tracking

#### Search Integration
- Remote documents appear in existing search results
- Add `source` field to search result metadata
- Support filtering by local vs remote content
- Update search UI to show source attribution

### 5. Configuration

#### New Config Options
```yaml
# server_config.yaml
remote_collection:
  temp_directory: "/tmp/repo_downloads"
  download_timeout: 300  # seconds
  max_repo_size: 100  # MB
  allowed_domains: ["github.com"]
  default_branch: "main"
  git_command: "git"  # Path to git executable
  cleanup_after_indexing: true
```

### 6. Error Handling and Edge Cases

#### Error Scenarios
- Invalid URLs
- Private repositories (no auth initially)
- Network failures
- Repository too large
- Git command failures
- Disk space exhaustion
- Timeout during download

#### Recovery Mechanisms
- Cleanup temporary files on failure
- Resume capability for interrupted downloads
- Clear error messages with actionable suggestions
- Logging of all operations

### 7. Security Considerations

#### Input Validation
- URL format validation
- Path traversal prevention
- File size limits
- Content type restrictions

#### Safe Execution
- Execute git in isolated temporary directories
- No execution of downloaded code
- Rate limiting considerations
- Audit logging

### 8. Dependencies

#### New Requirements
```
GitPython>=3.1.0
requests>=2.25.0
aiofiles>=0.6.0
```

#### System Requirements
- `git` command available in PATH
- Sufficient temporary disk space
- Network access to target URLs

### 9. Testing Strategy

#### Unit Tests
- URL parsing and validation
- Mock git operations
- Error condition handling
- Database integration

#### Integration Tests
- Small public repositories
- Various GitHub URL formats
- Network failure simulation
- Large repository handling

#### MCP Tool Tests
- Tool parameter validation
- Async operation handling
- Progress reporting
- Error response formats

### 10. Migration and Deployment

#### Database Migration
- Add new columns with default NULL values
- Backward compatible with existing data
- Migration script for existing installations

#### Configuration Migration
- Add new config section with sensible defaults
- Update documentation
- Version compatibility checks

#### Rollout Strategy
- Feature flag for gradual rollout
- Monitoring of new functionality
- Performance impact assessment
- User feedback collection

## Future Enhancements

### Phase 2 Features
- Authentication support (GitHub tokens, SSH keys)
- Incremental updates (fetch vs full clone)
- Repository metadata caching
- Content diff tracking
- Multi-format support (not just git repos)

### Phase 3 Features
- Generic URL support (documentation sites, APIs)
- Content scheduling (periodic updates)
- Repository health monitoring
- Integration with GitHub API for metadata

## Implementation Priority

1. **High Priority**: Basic GitHub repo cloning and indexing
2. **Medium Priority**: Error handling and security
3. **Medium Priority**: MCP tool interface
4. **Low Priority**: Advanced features (auth, incremental updates)

## Success Metrics

- Successfully index public GitHub repositories
- Search results include both local and remote content
- MCP tool provides clear feedback on collection progress
- No security vulnerabilities introduced
- Performance impact within acceptable limits