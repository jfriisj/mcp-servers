# Duplicate Detection and Bibliography Processing Workflow

## Current Situation
- 8 BibTeX export files from Primo (Mimer) searches
- Contains metadata + abstracts for ~1,381 papers
- Need systematic deduplication before proceeding with SLR

## Step 1: Combine and Deduplicate BibTeX Files

### Option A: Manual Processing (Recommended for Control)

#### 1. Combine All BibTeX Files
```bash
# In the papers directory
cat *.bib > combined_exports.bib
```

#### 2. Use Reference Manager for Deduplication
**Recommended tools:**
- **Zotero** (Free, excellent duplicate detection)
- **Mendeley** (Free, good for collaboration)
- **EndNote** (If available through institution)

**Process:**
1. Import combined_exports.bib into reference manager
2. Run automatic duplicate detection
3. Manually review potential duplicates
4. Export clean bibliography

### Option B: Command-Line Deduplication
Using bibutils or similar tools:

```bash
# Install bibutils if needed
# sudo apt-get install bibutils  # Linux
# brew install bibutils          # Mac
# choco install bibutils         # Windows

# Convert and process
bib2xml combined_exports.bib | xml2bib > cleaned_bibliography.bib
```

## Step 2: Manual Duplicate Analysis

### Common Duplicate Indicators
1. **Exact title matches** (most reliable)
2. **Same DOI** (perfect match)
3. **Same authors + similar titles** (likely duplicate)
4. **Same year + venue + similar title** (probable duplicate)

### Review Process
Create a duplicate review log:

```
DUPLICATE REVIEW LOG
Date: 2025-10-15
Reviewer: [Name]

Entry 1: [Citation]
Entry 2: [Citation]
Comparison:
- Title similarity: [Exact/High/Medium/Low]
- Author match: [Exact/Partial/None]
- DOI match: [Yes/No]
- Year match: [Yes/No]
Decision: [Keep Entry 1/Keep Entry 2/Keep Both]
Reason: [Explanation]
```

## Step 3: Expected Duplicate Patterns

### Likely Sources of Duplicates
1. **Same paper indexed in multiple databases** (IEEE + Springer)
2. **Conference vs. journal versions** (need decision rule)
3. **Preprint vs. published versions** (keep published)
4. **Different export formats** from same search

### Decision Rules for Near-Duplicates
1. **Conference vs. Journal**: Keep journal version if significantly expanded
2. **Preprint vs. Published**: Keep published version
3. **Multiple venues**: Keep version from higher-impact venue
4. **Different years**: Keep most recent if same content

## Step 4: Systematic Deduplication Process

### Phase 1: Automatic Detection (Day 1)
1. **Combine all BibTeX files**
2. **Import to reference manager**
3. **Run automatic duplicate detection**
4. **Export results with duplicate flags**

### Phase 2: Manual Review (Day 2-3)
1. **Review each potential duplicate pair**
2. **Apply decision rules consistently**
3. **Document all decisions**
4. **Create final clean bibliography**

### Phase 3: Quality Check (Day 4)
1. **Verify no obvious duplicates remain**
2. **Check for missing expected papers**
3. **Validate bibliography format**
4. **Prepare for SLR server upload**

## Step 5: Prepare for SLR Server Integration

### Convert to Individual Uploads
Since SLR server expects individual files, we need to:

1. **Extract key papers** from clean bibliography
2. **Download PDFs** for high-priority papers first
3. **Upload systematically** to SLR server
4. **Use server's duplicate detection** as secondary check

### Alternative: Create Structured Database
```python
# Example Python script to process BibTeX
import bibtexparser
import pandas as pd

# Load and combine all BibTeX files
combined_entries = []
for bib_file in ['Primo_BibTeX_Export.bib', 'Primo_BibTeX_Export (1).bib', ...]:
    with open(bib_file) as f:
        bib_db = bibtexparser.load(f)
        combined_entries.extend(bib_db.entries)

# Create DataFrame for analysis
df = pd.DataFrame(combined_entries)

# Duplicate detection based on titles
duplicates = df[df.duplicated(subset=['title'], keep=False)]
print(f"Found {len(duplicates)} potential duplicates")

# Export for manual review
duplicates.to_csv('potential_duplicates.csv', index=False)
```

## Step 6: Integration with SLR Server

### After Deduplication:
1. **Upload clean papers** individually to SLR server
2. **Use server tools** for additional duplicate checking:
   ```python
   # Check for duplicates in server
   papers = mcp_slr-server_list_papers()
   # Look for similar titles/authors
   ```

3. **Tag papers** with source information:
   ```python
   mcp_slr-server_upload_paper(
       file_path="paper.pdf",
       tags=["mimer_search", "batch_1", "deduplicated"]
   )
   ```

## Expected Results

### Deduplication Estimates
- **Starting papers**: ~1,381
- **Expected duplicates**: 200-400 (15-30%)
- **Clean bibliography**: ~1,000-1,200 unique papers
- **After abstract screening**: ~200-300 papers
- **Final included**: ~25-50 papers

### Quality Indicators
- ✅ No exact title duplicates
- ✅ No identical DOIs
- ✅ Clear decision rules applied
- ✅ All decisions documented
- ✅ Source tracking maintained

## Next Steps Recommendation

1. **Start with Zotero** for automatic duplicate detection
2. **Manual review** of flagged duplicates
3. **Create clean master bibliography**
4. **Begin systematic upload** to SLR server
5. **Use server tools** for additional quality checks

Would you like me to help you set up the Zotero import process or create a Python script for BibTeX analysis?