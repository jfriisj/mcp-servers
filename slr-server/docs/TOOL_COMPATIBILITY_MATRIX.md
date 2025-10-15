# SLR Server Tool Compatibility Matrix

Based on testing and implementation analysis, here's the current status of all SLR tools:

## ✅ **WORKING TOOLS** (Confirmed via MCP)

| Tool Name | Status | Implementation | Notes |
|-----------|--------|----------------|-------|
| `create_slr_project` | ✅ Working | Complete | Project management tool |
| `get_slr_progress` | ✅ Working | Complete | Progress tracking |
| `get_next_steps` | ✅ Working | Complete | AI recommendations |
| `get_slr_guide` | ✅ Working | Complete | Methodology guidance |
| `upload_paper` | ✅ Working | Complete | File upload with validation |
| `list_papers` | ✅ Working | Complete | Paper listing with filters |
| `get_paper` | ✅ Working | Complete | Paper details retrieval |
| `search_papers` | ✅ Working | Complete | Search functionality (may return no results if FTS not populated) |
| `validate_research_question` | ✅ Working | Complete | PICO/SPIDER validation |
| `create_screening_workflow` | ✅ Working | Complete | Screening setup |
| `screen_paper` | ✅ Working | Complete | Paper screening decisions |

## ⚠️ **PARTIALLY WORKING TOOLS** (Listed but Issues)

| Tool Name | Status | Issue | Workaround |
|-----------|--------|-------|------------|
| `index_paper` | ⚠️ Listed but not accessible | MCP mapping issue | Use direct service calls |
| `get_paper_structure` | ⚠️ Listed but not accessible | MCP mapping issue | Use direct service calls |
| `assess_quality` | ⚠️ Method missing | Not implemented in handler | Needs implementation |

## ❌ **NON-WORKING TOOLS** (Listed but Not Implemented)

| Tool Name | Status | Issue | Priority |
|-----------|--------|-------|----------|
| `analyze_citations` | ❌ Not implemented | Missing service implementation | High |
| `analyze_hypotheses` | ❌ Not implemented | Missing service implementation | Medium |
| `synthesize_evidence` | ❌ Not implemented | Missing service implementation | High |
| `generate_slr_report` | ❌ Not implemented | Missing service implementation | High |
| `export_citation_network` | ❌ Not implemented | Missing service implementation | Low |
| `calculate_inter_rater_reliability` | ❌ Not implemented | Missing service implementation | Medium |
| `detect_citation_patterns` | ❌ Not implemented | Missing service implementation | Low |

## 🔧 **QUICK FIXES NEEDED**

### 1. MCP Handler Mapping Issues

**Problem:** Some tools are listed in `list_slr_tools.py` but not accessible via MCP

**Root Cause:** Disconnect between tool definitions and actual MCP handler implementations

**Files to Fix:**
- `src/mcp_handler.py` - Add missing tool methods
- `src/server.py` - Ensure all tools are registered

### 2. Missing Service Implementations

**Problem:** Many advanced tools (citations, synthesis, reports) are not implemented

**Root Cause:** Services exist as stubs but lack actual implementation

**Files to Fix:**
- `src/services/hypothesis_analysis_service.py`
- `src/services/citation_analysis_service.py` 
- `src/services/synthesis_service.py`

### 3. Database Schema Issues

**Problem:** Field position mapping errors in repository

**Status:** ✅ FIXED - journal field positions corrected

## 📋 **RECOMMENDED TESTING ORDER**

Based on tool status, test in this order to avoid repeated errors:

### Phase 1: Core Workflow (All Working)
1. `create_slr_project` ✅
2. `upload_paper` ✅
3. `list_papers` ✅
4. `get_paper` ✅
5. `validate_research_question` ✅
6. `create_screening_workflow` ✅
7. `screen_paper` ✅

### Phase 2: Guidance Tools (All Working)
1. `get_slr_progress` ✅
2. `get_next_steps` ✅
3. `get_slr_guide` ✅

### Phase 3: Search Tools (Working but Limited)
1. `search_papers` ⚠️ (works but may return no results)

### Phase 4: Broken Tools (Skip Until Fixed)
- Skip all analysis, synthesis, and reporting tools until implementation is complete

## 🚨 **KNOWN ERROR PATTERNS**

### Error Pattern 1: Tool Not Found
```json
{"error": "Tool 'tool_name' not found", "type": "mcp_error"}
```
**Cause:** Tool not registered in MCP handler
**Solution:** Check `src/server.py` tool registration

### Error Pattern 2: Method Not Implemented
```json
{"error": "Tool 'assess_quality' has no method 'assess_quality'"}
```
**Cause:** Handler method missing
**Solution:** Implement method in `src/mcp_handler.py`

### Error Pattern 3: JSON Parsing Issues
```json
{"error": "the JSON object must be str, bytes or bytearray, not int"}
```
**Cause:** Field position mapping error
**Status:** ✅ FIXED

### Error Pattern 4: Database Constraint Errors
```json
{"error": "CHECK constraint failed: author_position > 0"}
```
**Cause:** Enumerate starting at 0 instead of 1
**Status:** ✅ FIXED

## 💡 **EFFICIENT TESTING STRATEGY**

### 1. Use Compatibility Matrix
- Only test tools marked as ✅ Working
- Skip tools marked as ❌ Not implemented
- Be cautious with ⚠️ Partially working tools

### 2. Follow Error Patterns
- If you encounter a known error pattern, apply the documented solution
- Don't spend time re-debugging the same issues

### 3. Batch Testing
- Test all working tools in sequence
- Document any new issues found
- Don't test broken tools repeatedly

### 4. Focus on Implementation Gaps
- Prioritize implementing missing services over debugging working tools
- Fix MCP mapping issues before testing

## 🎯 **NEXT PRIORITIES**

### Immediate (High Priority)
1. Fix MCP handler mapping for `index_paper` and `get_paper_structure`
2. Implement `assess_quality` method in handler
3. Implement `generate_slr_report` service

### Medium Priority
1. Implement citation analysis service
2. Implement evidence synthesis service
3. Add inter-rater reliability calculations

### Low Priority
1. Export functionality
2. Advanced pattern detection
3. Performance optimizations

## 🔄 **UPDATE PROTOCOL**

When testing reveals new information:

1. **Update this matrix** with current status
2. **Document new error patterns** with solutions
3. **Adjust testing priorities** based on findings
4. **Focus on gaps** rather than re-testing working tools

This matrix should be the **first reference** before any testing to avoid repeated errors and save time.