# Enhanced `get_paper` Function Feature

## Overview

The `get_paper` MCP tool has been enhanced to deliver comprehensive paper information including both abstract and full text extraction when available.

## What Changed

### Previous Behavior
The original `handle_get_paper` function returned only basic metadata:
```
Paper: {title}
Authors: {authors}
Year: {publication_year}
DOI: {doi}
```

### New Behavior
The enhanced function now returns comprehensive information organized in sections:

```
📄 **Paper ID:** {id}
📝 **Title:** {title}
✍️ **Authors:** {author names}
📅 **Year:** {publication_year}
🔗 **DOI:** {doi}
📚 **Journal:** {journal name}
📋 **File Type:** {file_type}
📖 **Pages:** {total_pages}

--- ABSTRACT ---
{abstract text or message if not available}

--- KEYWORDS ---
{comma-separated keywords}

--- FULL TEXT ---
{extracted text from PDF/DOCX/TXT, truncated to 5000 chars if needed}

--- METADATA ---
🔬 **Methodology:** {methodology}
📊 **Study Type:** {study_type}
📈 **Citations:** {citation_count}
🏷️ **Tags:** {tags}
✅ **Screening Status:** {screening_status}
📌 **Review Status:** {included/excluded with reason}
```

## Implementation Details

### File Modified
- `c:\github\mcp-servers\slr-server\src\handlers\mcp_handler.py`
  - Function: `handle_get_paper()`
  - Lines: ~117-207

### Key Features

#### 1. **Abstract Delivery**
- Retrieves and displays the paper's abstract if available
- Shows `[No abstract available]` if abstract is not present
- Useful for title-abstract screening phase in SLR workflows

#### 2. **Full Text Extraction**
- Automatically extracts full text from paper files (PDF, DOCX, TXT)
- Uses `document_service._extract_paper_content(paper)` for extraction
- **Smart Truncation**: Limits output to first 5,000 characters to prevent overwhelming responses
- Shows total text length and indicates truncation if needed
- Gracefully handles extraction failures with error messages

#### 3. **Comprehensive Metadata**
- **Publication Info**: Title, authors, year, DOI, journal
- **File Info**: File type, page count
- **Content Organization**: Keywords, methodology, study type
- **Quality Metrics**: Citation count
- **Screening Status**: Current screening phase, inclusion/exclusion status with reasons
- **Organization**: Tags and project assignment

#### 4. **Error Handling**
- Graceful handling of missing information (shows "None" or "[not available]")
- Robust error handling for file extraction failures
- Try-catch blocks for each extraction phase with informative messages

#### 5. **Human-Readable Output**
- Uses emoji indicators for quick visual scanning
- Clear section headers (ABSTRACT, FULL TEXT, METADATA)
- Well-formatted with newlines and indentation
- Markdown-friendly output for better readability

## Usage

### Via MCP Tool Call

The enhancement is transparent to users. Simply call `get_paper` as before:

```python
await handle_get_paper({"paper_id": 5})
```

The response will now include abstract and full text automatically.

### SLR Workflow Integration

#### Title-Abstract Screening
Perfect for reviewers during title-abstract phase:
```
1. Call get_paper(paper_id)
2. Review title + authors + abstract
3. Make inclusion/exclusion decision
4. Record decision via screen_paper tool
```

#### Full-Text Screening
Provides complete paper context:
```
1. Call get_paper(paper_id)
2. Review abstract to confirm scope
3. Read full text for detailed assessment
4. Record quality assessment
5. Extract data for synthesis
```

#### Quality Assessment
Supports comprehensive evaluation:
```
1. Access full metadata and content
2. Evaluate methodology and study design
3. Assess quality indicators (citations, publication venue)
4. Make final inclusion decision
```

## Benefits

### For Researchers
- **Complete Information**: No need to retrieve paper files separately
- **Efficient Screening**: Abstract + metadata in single call
- **Quality Control**: Full text available for verification
- **Audit Trail**: All paper data available for documentation

### For SLR Workflows
- **Streamlined Processing**: One API call provides complete paper data
- **Reduced Friction**: No context switching between systems
- **Better Decision Making**: Complete context available for screening decisions
- **Scalability**: Efficient batch processing with comprehensive metadata

### For MCP Integration
- **Consistent Interface**: Standardized response format
- **Rich Content**: Text, metadata, and analytics in one response
- **Error Resilience**: Handles various file types and extraction issues
- **Performance**: Smart truncation prevents overwhelming responses

## Technical Details

### Services Used
- **PaperRepository**: Retrieves paper metadata and relationships
- **ResearchDocumentService**: Extracts content from various file formats

### Content Extraction Capabilities
Supports extraction from:
- **PDF**: High-quality text extraction using PyMuPDF or PyPDF2
- **DOCX**: Word document content extraction
- **TXT/MD**: Plain text file reading
- **Abstract-only**: Metadata extraction when files not available

### Performance Considerations
- **Text Truncation**: 5,000 character limit prevents excessive output
- **Lazy Loading**: Only extracts content when requested
- **Error Handling**: Graceful fallback if extraction fails
- **Response Size**: Typically 2-10 KB depending on paper complexity

## Future Enhancements

Potential improvements for future versions:

1. **Configurable Truncation**
   ```python
   handle_get_paper({"paper_id": 5, "full_text_limit": 10000})
   ```

2. **Selective Content Retrieval**
   ```python
   handle_get_paper({
       "paper_id": 5, 
       "include": ["abstract", "full_text", "metadata"]
   })
   ```

3. **Format Options**
   ```python
   handle_get_paper({
       "paper_id": 5, 
       "format": "json"  # Instead of text
   })
   ```

4. **Content Caching**
   - Cache extracted full text to improve performance on repeated calls
   - Optional cache invalidation

5. **Citation Extraction**
   - Automatically extract and parse references from full text
   - Link to other papers in database

6. **Section Parsing**
   - Identify and separately extract paper sections (intro, methods, results, discussion)
   - Enable targeted content review

## Testing Recommendations

### Unit Tests
- Test with papers that have/don't have abstracts
- Test with various file types (PDF, DOCX, TXT)
- Test with missing files
- Test truncation logic with large files

### Integration Tests
- End-to-end screening workflow with full data retrieval
- Batch operations on multiple papers
- Error scenarios and graceful degradation

### Performance Tests
- Measure response time for various paper sizes
- Monitor memory usage during extraction
- Benchmark with large batches

## Migration Notes

No breaking changes - this enhancement is fully backward compatible.
Existing calls to `get_paper` will automatically receive enhanced output.

---

## Example Response

```
📄 **Paper ID:** 2
📝 **Title:** Tibetan–Chinese speech-to-speech translation based on discrete units
✍️ **Authors:** Gong, Zairan; Xu, Xiaona; Zhao, Yue
📅 **Year:** 2025
🔗 **DOI:** None
📚 **Journal:** None
📋 **File Type:** pdf
📖 **Pages:** 8

--- ABSTRACT ---
This paper presents a novel approach to Tibetan-Chinese speech-to-speech translation 
using discrete acoustic units. We propose a unified end-to-end framework that leverages 
hierarchical multilingual representations. Experimental results on the Tibetan-Chinese 
corpus demonstrate significant improvements over baseline approaches...

--- KEYWORDS ---
speech translation, multilingual, discrete units, neural networks

--- FULL TEXT ---
1. Introduction
Recent advances in neural machine translation have shown promising results...
[... truncated. Total length: 45832 characters ...]

--- METADATA ---
🔬 **Methodology:** Empirical
📊 **Study Type:** System Paper
📈 **Citations:** 3
🏷️ **Tags:** search-results, primo-export, speech-translation, abstract-screening
✅ **Screening Status:** pending
```

---

## Questions?

For more information about the SLR-server architecture or MCP tool integration, 
see the main documentation in `docs/` directory.
