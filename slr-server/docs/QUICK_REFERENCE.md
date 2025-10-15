# SLR Tools Quick Reference Card

## 🚀 **GUARANTEED WORKING TOOLS** (Test These First)

### Project Management
```python
# Create project (ALWAYS WORKS)
create_slr_project({
    "title": "Test SLR Project",
    "research_domain": "Healthcare",
    "description": "Test project for validation"
})

# Get progress (ALWAYS WORKS)
get_slr_progress({"project_id": 1})

# Get recommendations (ALWAYS WORKS)
get_next_steps({"project_id": 1, "current_phase": "planning"})
```

### Paper Management
```python
# Upload paper (WORKS - has validation)
upload_paper({
    "file_path": "/full/absolute/path/to/paper.pdf",
    "title": "Test Paper",
    "authors": ["Author One", "Author Two"],
    "tags": ["test", "validation"]
})

# List papers (ALWAYS WORKS)
list_papers({})

# Get paper details (ALWAYS WORKS)
get_paper({"paper_id": 1})
```

### Research Validation
```python
# Validate research question (ALWAYS WORKS)
validate_research_question({
    "research_question": "How effective are AI systems in healthcare?",
    "framework": "pico",
    "domain": "healthcare"
})
```

### Screening Workflow
```python
# Create screening workflow (ALWAYS WORKS)
create_screening_workflow({
    "project_id": 1,
    "inclusion_criteria": ["Peer-reviewed", "English"],
    "exclusion_criteria": ["Conference abstracts"],
    "reviewers": ["reviewer1", "reviewer2"],
    "screening_stages": ["title_abstract", "full_text"]
})

# Screen paper (ALWAYS WORKS)
screen_paper({
    "project_id": 1,
    "paper_id": 1,
    "reviewer_id": "reviewer1",
    "stage": "title_abstract",
    "decision": "include",
    "reason": "Meets inclusion criteria"
})
```

## ⚠️ **SKIP THESE TOOLS** (Broken/Not Implemented)

```bash
# DON'T TEST THESE - THEY'RE BROKEN:
- analyze_citations         # Not implemented
- analyze_hypotheses       # Not implemented  
- synthesize_evidence      # Not implemented
- generate_slr_report      # Not implemented
- export_citation_network  # Not implemented
- assess_quality          # Method missing
- index_paper             # MCP mapping issue
- get_paper_structure     # MCP mapping issue
```

## 🔧 **COMMON ERROR FIXES**

### Error: "Tool not found"
**Solution:** Check tool name spelling, use tools from "GUARANTEED WORKING" list

### Error: "File not found"
**Solution:** Use absolute paths, verify file exists:
```bash
# Check file exists (Windows)
dir "C:\full\path\to\file.pdf"
# Check file exists (Linux/Mac)
ls -la "/full/path/to/file.pdf"
```

### Error: "JSON constraint failed"
**Status:** ✅ FIXED - If you still see this, restart server

### Error: "Method not implemented"
**Solution:** Tool is listed but not implemented - skip it for now

## 📋 **EFFICIENT TEST SEQUENCE**

### 1. Basic Workflow Test (5 minutes)
```python
# Test core functionality in order:
project = create_slr_project({...})         # ✅
paper = upload_paper({...})                  # ✅  
papers = list_papers({})                     # ✅
details = get_paper({"paper_id": 1})         # ✅
progress = get_slr_progress({"project_id": 1}) # ✅
```

### 2. Extended Workflow Test (10 minutes)
```python
# Add validation and screening:
validation = validate_research_question({...}) # ✅
workflow = create_screening_workflow({...})    # ✅
screening = screen_paper({...})                # ✅
guidance = get_slr_guide({...})               # ✅
```

### 3. Search Test (2 minutes)
```python
# Test search (may return empty results):
results = search_papers({"query": "test"})    # ⚠️ Works but may be empty
```

## 🎯 **TESTING PRIORITIES**

### ✅ **HIGH CONFIDENCE** - Test these anytime
- All project management tools
- All paper management tools  
- All screening tools
- All guidance tools

### ⚠️ **MEDIUM CONFIDENCE** - Test with caution
- `search_papers` (works but may return no results)

### ❌ **LOW CONFIDENCE** - Skip for now
- All analysis tools
- All synthesis tools  
- All reporting tools
- Assessment tools

## 🚨 **STOP TESTING IF...**

1. **Same error repeats 3+ times** → Check this matrix first
2. **Tool not found errors** → Use guaranteed working tools list
3. **Method missing errors** → Skip that tool, it's not implemented
4. **File path errors** → Fix paths before continuing

## 📈 **SUCCESS METRICS**

### Minimal Success (Core Working)
- ✅ Can create project
- ✅ Can upload paper
- ✅ Can list papers
- ✅ Can screen papers

### Full Success (Extended Working)  
- ✅ All above + validation tools
- ✅ All above + guidance tools
- ✅ All above + progress tracking

### Advanced Success (When Implemented)
- ✅ All above + quality assessment
- ✅ All above + analysis tools
- ✅ All above + reporting tools

## 💡 **TIME-SAVING TIPS**

1. **Always check this matrix first** before testing any tool
2. **Use absolute file paths** to avoid path issues
3. **Test guaranteed tools first** to validate server is working
4. **Don't debug the same error twice** - document solutions here
5. **Focus on implementation gaps** rather than re-testing working tools

---

**Last Updated:** Based on comprehensive testing and implementation analysis
**Next Update:** After implementing missing service methods