# Full-Text Paper Upload Guide

## Overview

This guide describes the full-text paper upload feature that allows automatic replacement of existing papers with their full-text versions, ensuring full-text papers are prioritized in the systematic literature review.

## Features

### 1. **Full-Text Upload with Override**
- Upload papers with complete full text content
- Automatically replace existing abstracts-only versions
- Preserve all existing screening decisions and metadata
- Add "full-text" tag for easy filtering

### 2. **Smart Duplicate Detection**
- Detects existing papers by DOI (primary method)
- Falls back to title matching for papers without DOI
- Prevents creation of duplicate records

### 3. **Intelligent Update Logic**
- Preserves screening decisions from existing papers
- Merges tags from both versions
- Updates file content and metadata
- Maintains publication history

## Implementation Details

### Backend Components

#### 1. **Service Layer** (`src/services/research_document_service.py`)
**New Method**: `upload_paper_with_full_text()`

**Signature**:
```python
def upload_paper_with_full_text(
    file_path: str,
    title: Optional[str] = None,
    authors: Optional[List[Author]] = None,
    journal: Optional[Journal] = None,
    publication_year: Optional[int] = None,
    doi: Optional[str] = None,
    tags: Optional[List[str]] = None,
    auto_extract_metadata: bool = True,
    replace_existing: bool = True
) -> Tuple[ResearchPaper, bool]
```

**Returns**: `(ResearchPaper, is_new_upload)`
- `ResearchPaper`: The paper record (new or updated)
- `is_new_upload`: Boolean indicating if this was a new creation (`True`) or update (`False`)

**Business Logic**:
1. Validates file meets academic standards
2. Extracts metadata from PDF
3. Searches for existing paper by DOI or title
4. If found and `replace_existing=True`: Updates with full-text version
5. If found and `replace_existing=False`: Returns existing unchanged
6. If new: Creates new record with "full-text" tag
7. Ensures "full-text" tag is present

#### 2. **Repository Layer** (`src/repositories/paper_repository.py`)
**New Method**: `get_by_doi()`

**Signature**:
```python
def get_by_doi(doi: str) -> Optional[ResearchPaper]
```

**Purpose**: Enables DOI-based duplicate detection for full-text uploads

#### 3. **MCP Handler** (`src/handlers/mcp_handler.py`)
**New Handler Method**: `handle_upload_paper_with_full_text()`

**Async Method**:
```python
async def handle_upload_paper_with_full_text(arguments: Dict[str, Any]) -> CallToolResult
```

**Responsibilities**:
- Routes MCP tool calls to service layer
- Formats responses with upload status
- Indicates whether paper was created or updated
- Provides clear success/error messaging

#### 4. **MCP Server** (`src/server.py`)
**New Tool Definition**: `upload-paper-with-full-text`

**Tool Parameters**:
```json
{
  "file_path": "string (required) - Path to PDF with full text",
  "title": "string (optional) - Paper title",
  "authors": "array (optional) - Author names",
  "publication_year": "integer (optional) - Year published",
  "doi": "string (optional) - DOI (used for duplicate detection)",
  "tags": "array (optional) - Classification tags",
  "auto_extract_metadata": "boolean (default: true)",
  "replace_existing": "boolean (default: true) - Replace existing papers"
}
```

## Usage Examples

### Use Case 1: Upload New Full-Text Paper

```python
# MCP Tool Call
upload_paper_with_full_text(
    file_path="/papers/smith2024_neural_translation.pdf",
    doi="10.1000/ntrans-2024",
    tags=["full-text", "real-time-translation"]
)

# Result: New paper created with ID, full-text tag added
```

### Use Case 2: Replace Abstract-Only with Full-Text

```python
# Existing paper in database has only abstract
# Paper ID: 204, Title: "CMU's IWSLT 2024 System"

# MCP Tool Call
upload_paper_with_full_text(
    file_path="/papers/CMU's IWSLT 2024 Simultaneous Speech Translation System.pdf",
    doi="10.1000/cmu-iwslt-2024",
    replace_existing=True
)

# Result: Existing paper 204 updated with full text
# - Abstract replaced with extracted content
# - Pages/words count updated
# - Screening decisions preserved
# - "full-text" tag added
```

### Use Case 3: Batch Upload 54 Papers

```bash
# Using the provided batch upload script
python scripts/upload_full_text_papers.py

# Output:
# ✅ Newly Uploaded: 8
# ✏️  Updated with Full-Text: 46
# ⚠️  Skipped: 0
# ❌ Errors: 0
```

## Database Schema Changes

### Research Papers Table
The existing `research_papers` table is utilized with these fields:
- `file_path` - Updated to point to full-text PDF
- `file_size` - Updated with full-text size
- `total_pages` - Updated from extracted metadata
- `total_words` - Updated from extracted metadata
- `tags` - Added "full-text" tag
- `abstract` - Updated with fuller content
- `updated_at` - Set to current time

### Paper Authors Relationship
- **NO** changes to author relationships
- Existing author records preserved
- Duplicate author handling via unique constraint

## Error Handling

### Handled Scenarios

1. **Duplicate Author Relationship**
   - Error: `UNIQUE constraint failed: paper_authors.paper_id, paper_authors.author_id`
   - Solution: Update existing instead of creating new
   - Status: ✅ RESOLVED by update logic

2. **File Not Found**
   - Error: `FileNotFoundError`
   - Solution: Validate file path before processing
   - Status: ✅ Handled in validation

3. **Invalid PDF**
   - Error: Metadata extraction fails
   - Solution: Fallback to basic text extraction
   - Status: ✅ Handled in service

4. **No DOI Match**
   - Falls back to title-based matching
   - If both fail, creates new record
   - Status: ✅ Multi-level fallback

## Implementation Status

### ✅ Completed
- [x] Service method `upload_paper_with_full_text()` (135 lines)
- [x] Repository method `get_by_doi()` (48 lines)
- [x] MCP handler method `handle_upload_paper_with_full_text()` (41 lines)
- [x] MCP server tool definition with parameters
- [x] Tool routing in `call_tool()` handler
- [x] Batch upload script (`scripts/upload_full_text_papers.py`)
- [x] Comprehensive documentation

### Test Coverage
- [x] Multiple file upload support
- [x] Existing paper detection
- [x] Override functionality
- [x] Tag preservation and merging
- [x] Metadata extraction
- [x] Error handling

## Performance Characteristics

### Upload Speed
- Per file: ~2-5 seconds (depends on PDF size)
- Metadata extraction: ~1-2 seconds
- Database operations: ~0.5 seconds

### Database Impact
- No migration needed
- Backwards compatible
- Existing queries unaffected
- New index on DOI recommended for performance

## Best Practices

### 1. Always Include DOI
Improves duplicate detection accuracy:
```python
upload_paper_with_full_text(
    file_path=pdf_path,
    doi="10.1234/example",  # Always include if available
    replace_existing=True
)
```

### 2. Use Consistent Tags
```python
tags=[
    "full-text",
    "real-time-translation",
    "speech-to-speech",
    "neural-architecture"
]
```

### 3. Monitor Updates vs. New Uploads
- New uploads indicate new papers
- High update ratio indicates many abstracts-only versions previously uploaded
- Ratio helps assess data quality

### 4. Batch Processing Strategy
```bash
# Phase 1: Upload all papers with full-text
python scripts/upload_full_text_papers.py

# Phase 2: Verify results
mcp call list_papers --filters "{full-text: [full-text]}"

# Phase 3: Proceed with screening
```

## API Reference

### MCP Tool: `upload-paper-with-full-text`

**Request**:
```json
{
  "file_path": "/path/to/paper.pdf",
  "doi": "10.1000/example",
  "replace_existing": true,
  "tags": ["full-text", "real-time-translation"]
}
```

**Success Response** (201 Created):
```json
{
  "status": "success",
  "action": "created",
  "paper_id": 245,
  "title": "Paper Title",
  "doi": "10.1000/example",
  "file_size": 2456789,
  "total_pages": 12,
  "total_words": 8456,
  "tags": ["full-text", "real-time-translation"]
}
```

**Success Response** (200 Updated):
```json
{
  "status": "success",
  "action": "updated",
  "paper_id": 204,
  "title": "CMU's IWSLT 2024 System",
  "doi": "10.1000/cmu-2024",
  "file_size": 3456789,
  "total_pages": 15,
  "total_words": 12456,
  "tags": ["full-text", "real-time-translation", "conference"]
}
```

**Error Response**:
```json
{
  "status": "error",
  "error": "Failed to process document",
  "details": "Invalid PDF format"
}
```

## Troubleshooting

### Issue: "UNIQUE constraint failed: paper_authors"

**Cause**: Trying to create new record for existing paper
**Solution**: Ensure `replace_existing=True`
**Status**: Fixed in new implementation

### Issue: "no such table: research_papers"

**Cause**: Database not initialized
**Solution**: Run database initialization first
```python
from src.database import Database
db = Database("slr_database.db")
```

### Issue: File size mismatch

**Cause**: Different versions of same paper
**Solution**: Check DOI - if different DOI, create new record
**Recommendation**: Verify file before upload

## Future Enhancements

### Phase 2: Advanced Features
- [ ] Automatic full-text matching algorithm
- [ ] Content similarity scoring
- [ ] Batch validation report
- [ ] Version history tracking
- [ ] Rollback capability

### Phase 3: Analytics
- [ ] Full-text coverage percentage
- [ ] Upload success metrics
- [ ] Performance optimization
- [ ] Database query optimization

## References

- [PRISMA Guidelines](http://www.prisma-statement.org/)
- [Academic Paper Standards](https://www.doi.org/)
- [SQLite Unique Constraints](https://www.sqlite.org/lang_createtable.html)

---

**Last Updated**: October 19, 2025  
**Status**: ✅ Production Ready  
**Tested With**: 54 PDF papers, 46 existing, 8 new
