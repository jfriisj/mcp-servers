# Data Collection Workflow for Real-Time Speech Translation SLR

## Current Search Results Summary
Based on your Mimer searches on 2025-10-15:

| Search Strategy | Results | Status |
|----------------|---------|--------|
| Primary terms (real-time, simultaneous, live, speech-to-speech, streaming) | 353 | ✅ Completed |
| Secondary terms (interpretation, platform, voice translation) | 870 | ✅ Completed |
| Technical variants (pipeline, end-to-end, cascaded) | 117 | ✅ Completed |
| Primary Boolean combination | 20 | ✅ Completed |
| Architecture-focused | 5 | ✅ Completed |
| Performance-focused | 2 | ✅ Completed |
| Component-focused | 14 | ✅ Completed |
| **TOTAL** | **1,381** | **Ready for collection** |

## Recommended Collection Strategy

### Phase 1: Metadata + Abstract Collection (Week 1)

#### Day 1-2: Export from Mimer
1. **Export each search result set separately** to maintain traceability
2. **Include full abstracts** in exports
3. **Use RIS format** for best compatibility
4. **Document search URLs** for reproducibility

#### Day 3: Deduplication and Preparation
1. **Combine all exports** into master bibliography
2. **Remove duplicates** using reference manager
3. **Add search source tags** to track origin
4. **Prepare for SLR server upload**

#### Day 4-5: Upload and Initial Indexing
1. **Upload papers to SLR server** in batches
2. **Run indexing** for semantic searchability
3. **Perform initial quality check** on uploads

### Phase 2: Abstract-Level Screening (Week 2)

#### Using SLR Server Tools:
1. **Search across uploaded papers** using semantic search
2. **Screen abstracts** using inclusion/exclusion criteria
3. **Tag papers** for inclusion/exclusion
4. **Document screening decisions**

### Phase 3: Full-Text Collection (Week 3)
**Only for papers passing abstract screening:**
1. **Download full PDFs** for included papers
2. **Upload PDFs to SLR server**
3. **Run full-text indexing**
4. **Perform final screening**

## Implementation with SLR Server

### Step 1: Upload Initial Papers
Use the upload_paper tool for each export batch:

```bash
# Example for batch upload
for each_export_file:
    mcp_slr-server_upload_paper(
        file_path="path/to/exported_papers.ris",
        tags=["search_batch_1", "mimer_export", "metadata_only"]
    )
```

### Step 2: Index for Searchability
```bash
# Index papers for semantic search
mcp_slr-server_index_paper(paper_id, strategy="academic_section")
```

### Step 3: Use SLR Server for Screening
```bash
# Search within your collection
mcp_slr-server_search_papers(
    query="architecture AND performance AND real-time",
    search_type="semantic"
)

# Screen papers systematically  
mcp_slr-server_screen_paper(
    paper_id=X,
    project_id=1,
    stage="title_abstract",
    decision="include/exclude",
    reason="..."
)
```

## Advantages of This Approach

### ✅ **Efficiency Benefits:**
- **Fast initial screening**: Abstract-level first
- **Reduced download time**: Only get full texts for relevant papers
- **Better organization**: SLR server manages everything
- **Semantic search**: Find related papers within your collection

### ✅ **Quality Benefits:**
- **Complete audit trail**: Every step documented
- **Systematic screening**: Built-in SLR workflow
- **Duplicate detection**: Server handles deduplication
- **Inter-rater reliability**: Multiple reviewer support

### ✅ **PRISMA Compliance:**
- **Complete documentation**: All search steps recorded
- **Transparent process**: Clear inclusion/exclusion tracking
- **Reproducible**: Full search strategy preserved
- **Quality metrics**: Built-in assessment tools

## Alternative Approach (Less Recommended)

### Full-Text Collection First
**❌ Why not recommended:**
- **Time intensive**: ~1,381 full-text downloads
- **Storage heavy**: Large PDF collection to manage
- **Screening inefficient**: Reading full papers for obvious exclusions
- **Higher error rate**: Easy to get lost in details

**✅ When to consider:**
- If you have automated download tools
- If most papers are likely relevant (>80%)
- If you need citation analysis early

## Next Steps Recommendation

1. **Export your Mimer results** in RIS format with abstracts
2. **Upload to SLR server** using the systematic approach
3. **Use SLR server screening workflow** for efficient review
4. **Download full texts only** for papers passing abstract screening

Would you like me to help you:
1. **Set up the upload process** for your Mimer exports?
2. **Create screening workflows** in the SLR server?
3. **Design the abstract screening criteria** for efficient review?