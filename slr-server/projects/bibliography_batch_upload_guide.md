# Bibliography Batch Upload Service

## Overview
Enhanced SLR server now supports BibTeX (.bib) and RIS (.ris) formats for bibliography imports. This enables efficient batch uploading of search results from academic databases.

## New Features Added

### 1. File Format Support
- ✅ **BibTeX (.bib)**: Full metadata extraction including abstracts, authors, keywords, DOI
- ✅ **RIS (.ris)**: Research Information Systems format support
- ✅ **Multiple entries**: Each bibliography file can contain multiple papers
- ✅ **Enhanced parsing**: Improved metadata extraction with academic validation

### 2. Updated Components

#### Models (models.py)
```python
valid_file_types = {"pdf", "docx", "txt", "md", "bib", "ris"}
```

#### Service Layer (research_document_service.py)
```python
ACADEMIC_EXTENSIONS = {'.pdf', '.docx', '.tex', '.bib', '.ris'}
```

#### Database Schema (schema.py)
```python
file_type IN ('pdf', 'txt', 'html', 'xml', 'docx', 'bib', 'ris')
```

### 3. Metadata Extraction Capabilities

#### BibTeX Extraction
- **Title**: From `title` field
- **Authors**: Parsed from `author` field (handles "and" separators)
- **Abstract**: From `abstract` field
- **Keywords**: From `keywords` field
- **Year**: From `year` field
- **DOI**: From `doi` field
- **Journal**: From `journal` field
- **Multiple entries**: Tracks total number of entries in file

#### RIS Extraction
- **Title**: From `TI -` field
- **Authors**: From multiple `AU -` fields
- **Abstract**: From `AB -` field
- **Keywords**: From `KW -` fields (semicolon separated)
- **Year**: From `PY -` field
- **DOI**: From `DO -` field
- **Journal**: From `JO -` field

## Usage Instructions

### 1. Upload Single Bibliography File
```python
# Now works with your BibTeX exports
result = mcp_slr-server_upload_paper(
    file_path="c:/github/mcp-servers/slr-server/papers/Primo_BibTeX_Export.bib",
    tags=["mimer_export", "batch_1", "metadata_abstracts"]
)
```

### 2. Upload All Your Exported Files
```python
# Upload each of your 8 BibTeX files
files = [
    "Primo_BibTeX_Export.bib",
    "Primo_BibTeX_Export (1).bib", 
    "Primo_BibTeX_Export (2).bib",
    "Primo_BibTeX_Export (3).bib",
    "Primo_BibTeX_Export (4).bib",
    "Primo_BibTeX_Export (5).bib",
    "Primo_BibTeX_Export (6).bib",
    "Primo_BibTeX_Export (7).bib"
]

for i, file in enumerate(files):
    mcp_slr-server_upload_paper(
        file_path=f"c:/github/mcp-servers/slr-server/papers/{file}",
        tags=[f"mimer_batch_{i+1}", "bibliography_import", "search_results"]
    )
```

## Duplicate Detection Strategy

### 1. Automatic Detection
The SLR server will now:
- ✅ **DOI matching**: Automatically detect papers with same DOI
- ✅ **Title similarity**: Flag potential duplicates based on title matching
- ✅ **Author overlap**: Consider author combinations for duplicate detection

### 2. Manual Review Process
After uploading, use these commands to check for duplicates:

```python
# List all uploaded papers
papers = mcp_slr-server_list_papers()

# Search for potential duplicates by title/author similarity
search_results = mcp_slr-server_search_papers(
    query="duplicate title or author patterns",
    search_type="semantic"
)
```

### 3. Quality Control
```python
# Screen papers systematically
mcp_slr-server_screen_paper(
    paper_id=X,
    project_id=1,
    stage="title_abstract", 
    decision="include/exclude",
    reason="duplicate/not_relevant/etc"
)
```

## Expected Workflow

### Step 1: Upload All Bibliography Files
- Upload your 8 BibTeX files from Mimer
- Each file will extract metadata from first entry
- Tag with source information for tracking

### Step 2: Systematic Duplicate Detection
- Use SLR server's search capabilities
- Cross-reference DOIs, titles, authors
- Document all duplicate decisions

### Step 3: Screening Workflow
- Screen at abstract level first
- Use inclusion/exclusion criteria
- Progress through systematic review stages

### Step 4: Full-Text Collection
- Download PDFs only for included papers
- Upload PDFs to replace bibliography entries
- Continue with data extraction

## Benefits of This Approach

### ✅ **Efficiency**
- Direct import of search results
- No manual data entry required
- Automated metadata extraction

### ✅ **Quality Control**
- Built-in validation
- Academic format compliance
- Systematic duplicate detection

### ✅ **PRISMA Compliance**
- Full audit trail maintained
- Search strategy documented
- Screening decisions tracked

### ✅ **Scalability**
- Handle large bibliography collections
- Batch processing capabilities
- Systematic organization

## Next Steps

1. **Test Upload**: Start with one BibTeX file to verify functionality
2. **Batch Upload**: Process all 8 files systematically
3. **Duplicate Review**: Use server tools for deduplication
4. **Screening**: Begin systematic abstract-level screening
5. **Full-Text**: Download and upload PDFs for included papers

You can now proceed with uploading your Primo BibTeX exports directly to the SLR server!