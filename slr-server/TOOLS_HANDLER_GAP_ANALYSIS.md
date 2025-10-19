# 🔍 MCP Tools Handler - Feature Analysis & Gap Report

**Date**: October 19, 2025  
**Status**: Comprehensive Analysis Complete

---

## 📊 Tools Coverage Summary

### Tools Defined in server.py (Tool List)
1. ✅ `upload-paper`
2. ✅ `upload-paper-with-full-text`
3. ✅ `assess-quality`
4. ✅ `validate-research-question`
5. ✅ `analyze-citations`
6. ✅ `test-hypothesis`
7. ✅ `index-paper`
8. ✅ `synthesize-evidence`

### Handler Methods Available in mcp_handler.py
1. ✅ `handle_upload_paper`
2. ✅ `handle_upload_paper_with_full_text`
3. ✅ `handle_upload_bibliography_batch`
4. ✅ `handle_get_paper`
5. ✅ `handle_list_papers`
6. ✅ `handle_assess_quality`
7. ✅ `handle_get_quality_assessment`
8. ✅ `handle_search_papers`
9. ✅ `handle_index_paper`
10. ✅ `handle_get_paper_structure`
11. ✅ `handle_analyze_citations`
12. ✅ `handle_synthesize_evidence`
13. ✅ `handle_generate_slr_report`
14. ✅ `handle_detect_remove_duplicates`
15. ✅ `handle_create_slr_project`

### Tool Routing in call_tool() (server.py)
1. ✅ `upload-paper` → `handler.upload_paper()`
2. ✅ `upload-paper-with-full-text` → `handler.upload_paper_with_full_text()`
3. ✅ `assess-quality` → `handler.assess_quality()` [BUT METHOD DOESN'T MATCH]
4. ✅ `validate-research-question` → `handler.validate_research_question()` [BUT METHOD DOESN'T MATCH]
5. ✅ `analyze-citations` → `handler.analyze_citations()` [BUT METHOD DOESN'T MATCH]
6. ✅ `test-hypothesis` → `handler.test_hypothesis()` [BUT METHOD DOESN'T MATCH]
7. ✅ `index-paper` → `handler.index_paper()` [BUT METHOD DOESN'T MATCH]
8. ✅ `synthesize-evidence` → `handler.synthesize_evidence()` [BUT METHOD DOESN'T MATCH]

---

## 🚨 CRITICAL GAPS IDENTIFIED

### 1. **Method Name Mismatch** (HIGH PRIORITY)

#### Problem
The server.py routing calls snake_case method names, but the handlers use `handle_*` prefixed names.

**Example**:
```python
# server.py tries to call:
result = handler.upload_paper(...)

# But mcp_handler.py defines:
async def handle_upload_paper(self, arguments)
```

#### Impact
- ❌ Tools will fail when called via MCP
- ❌ AttributeError: "SLRMCPHandler has no attribute 'upload_paper'"
- ❌ All tool routing except first 2 are broken

#### Solution Required
Create wrapper methods or fix routing. Two options:

**Option A: Add wrapper methods to SLRMCPHandler**
```python
# Add these methods to mcp_handler.py:
async def upload_paper(self, **kwargs):
    return await self.handle_upload_paper(kwargs)

async def assess_quality(self, **kwargs):
    return await self.handle_assess_quality(kwargs)

# ... etc for all tools
```

**Option B: Update routing in server.py**
```python
# Change calls to use handle_ prefix:
if name == "assess-quality":
    result = await handler.handle_assess_quality(arguments)

if name == "upload-bibliography-batch":
    result = await handler.handle_upload_bibliography_batch(arguments)
```

---

### 2. **Missing Tool Definitions** (MEDIUM PRIORITY)

#### Handlers with no MCP Tool Definition
These handlers exist but aren't exposed as MCP tools:

| Handler Method | Tool Name | Status |
|---|---|---|
| `handle_upload_bibliography_batch` | ❌ Not defined | Handlers 3/8 |
| `handle_get_paper` | ❌ Not defined | Handlers 4/8 |
| `handle_list_papers` | ❌ Not defined | Handlers 5/8 |
| `handle_get_quality_assessment` | ❌ Not defined | Handlers 7/8 |
| `handle_search_papers` | ❌ Not defined | Handlers 8/8 |
| `handle_get_paper_structure` | ❌ Not defined | Handlers 10/8 |
| `handle_generate_slr_report` | ❌ Not defined | Handlers 13/8 |
| `handle_detect_remove_duplicates` | ❌ Not defined | Handlers 14/8 |
| `handle_create_slr_project` | ❌ Not defined | Handlers 15/8 |

#### Missing Workflow Tools
These handlers from `SLRWorkflowMCPHandler` are NOT in the main handler:

| Method | Status |
|---|---|
| `handle_get_slr_progress` | ❌ Not routed |
| `handle_get_next_steps` | ❌ Not routed |
| `handle_get_slr_guide` | ❌ Not routed |
| `handle_screen_paper` | ❌ Not routed |

### Impact
- ⚠️ 9 useful handlers are inaccessible via MCP tools
- ⚠️ Users can't perform critical operations:
  - Can't list papers
  - Can't search papers
  - Can't get paper details
  - Can't generate reports
  - Can't detect duplicates
  - Can't manage projects
  - Can't screen papers

---

### 3. **Async/Await Issues** (HIGH PRIORITY)

#### Problem
The call_tool() routing code is synchronous, but all handlers are async.

**Current Code** (BROKEN):
```python
@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    try:
        result = None
        
        if name == "assess-quality":
            result = handler.assess_quality(...)  # ❌ Doesn't await async call!
            
        return [types.TextContent(...)]
```

#### Impact
- ❌ Tools don't actually wait for completion
- ❌ Results are coroutine objects, not actual results
- ❌ Client gets error or incomplete data

#### Solution Required
Either:
1. Make handlers synchronous (not async)
2. Add `await` to all handler calls
3. Use asyncio.run() wrapper

```python
# Fix Option 1: Add await
if name == "assess-quality":
    result = await handler.handle_assess_quality(arguments)

# Fix Option 2: Handle coroutine
if name == "assess-quality":
    coro = handler.assess_quality(...)
    result = await coro
```

---

### 4. **Missing Tool Routing Cases** (HIGH PRIORITY)

#### Tools defined but NOT routed
```python
# Tool is defined in server.py but NOT in call_tool() switch:
elif name == "get-paper":
    # ❌ No routing case!

elif name == "list-papers":
    # ❌ No routing case!
    
elif name == "search-papers":
    # ❌ No routing case!

elif name == "get-quality-assessment":
    # ❌ No routing case!

elif name == "generate-slr-report":
    # ❌ No routing case!

elif name == "detect-remove-duplicates":
    # ❌ No routing case!

elif name == "create-slr-project":
    # ❌ No routing case!
```

#### Result
- ✅ Tool is listed (so user sees it)
- ❌ Tool call fails with "Unknown tool" error
- ❌ User gets: `{"success": false, "error": "Unknown tool: get-paper"}`

---

## 📋 Complete Tool Coverage Matrix

| Tool Name | Tool Defined | Handler Exists | Routed | Async Fixed | Status |
|---|---|---|---|---|---|
| upload-paper | ✅ | ✅ | ✅ | ⚠️ | 🟡 PARTIAL |
| upload-paper-with-full-text | ✅ | ✅ | ✅ | ⚠️ | 🟡 PARTIAL |
| upload-bibliography-batch | ❌ | ✅ | ❌ | N/A | 🔴 NOT EXPOSED |
| get-paper | ⏳ | ✅ | ❌ | N/A | 🔴 BROKEN |
| list-papers | ⏳ | ✅ | ❌ | N/A | 🔴 BROKEN |
| assess-quality | ✅ | ✅ | ✅ | ⚠️ | 🟡 PARTIAL |
| get-quality-assessment | ❌ | ✅ | ❌ | N/A | 🔴 NOT EXPOSED |
| search-papers | ❌ | ✅ | ❌ | N/A | 🔴 NOT EXPOSED |
| index-paper | ✅ | ✅ | ✅ | ⚠️ | 🟡 PARTIAL |
| get-paper-structure | ❌ | ✅ | ❌ | N/A | 🔴 NOT EXPOSED |
| analyze-citations | ✅ | ✅ | ✅ | ⚠️ | 🟡 PARTIAL |
| test-hypothesis | ✅ | ✅ | ✅ | ⚠️ | 🟡 PARTIAL |
| synthesize-evidence | ✅ | ✅ | ✅ | ⚠️ | 🟡 PARTIAL |
| generate-slr-report | ❌ | ✅ | ❌ | N/A | 🔴 NOT EXPOSED |
| detect-remove-duplicates | ❌ | ✅ | ❌ | N/A | 🔴 NOT EXPOSED |
| create-slr-project | ❌ | ✅ | ❌ | N/A | 🔴 NOT EXPOSED |

**Summary**:
- ✅ Full: 0/16
- 🟡 Partial: 8/16 (50%)
- 🔴 Broken: 8/16 (50%)

---

## 🔧 High-Priority Issues to Fix

### Issue #1: Async/Await Mismatch
**Severity**: 🔴 CRITICAL

```python
# CURRENT (BROKEN):
@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    result = handler.upload_paper(...)  # Returns coroutine, not awaited!

# FIXED:
@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    result = await handler.handle_upload_paper(arguments)
```

### Issue #2: Method Name Mismatch
**Severity**: 🔴 CRITICAL

```python
# CURRENT (BROKEN):
result = handler.upload_paper(...)

# FIXED (Option A - add wrapper):
async def upload_paper(self, arguments):
    return await self.handle_upload_paper(arguments)

# FIXED (Option B - rename routing):
result = await handler.handle_upload_paper(arguments)
```

### Issue #3: Missing Route Cases
**Severity**: 🟡 HIGH

Add routing for all defined tools:
```python
elif name == "get-paper":
    result = await handler.handle_get_paper(arguments)
elif name == "list-papers":
    result = await handler.handle_list_papers(arguments)
elif name == "search-papers":
    result = await handler.handle_search_papers(arguments)
# ... etc
```

### Issue #4: Add Missing Tool Definitions
**Severity**: 🟡 HIGH

Define these tools in server.py:
- `upload-bibliography-batch`
- `get-quality-assessment`
- `get-paper-structure`
- `generate-slr-report`
- `detect-remove-duplicates`
- `create-slr-project`

---

## ✨ Missing Features Summary

| Feature | Status | Impact |
|---|---|---|
| Full paper CRUD | 🔴 | Can't read/list/search papers |
| Quality management | 🔴 | Can't retrieve assessments |
| Paper structure analysis | 🔴 | Can't analyze document structure |
| Report generation | 🔴 | Can't generate SLR reports |
| Duplicate detection | 🔴 | Can't find/remove duplicates |
| Project management | 🔴 | Can't create/manage projects |
| Batch bibliography | 🔴 | Can't batch upload BibTeX |
| Screening workflow | 🔴 | Can't screen papers programmatically |

---

## 🎯 Recommended Priority Order

### Phase 1: CRITICAL FIXES (Do First)
1. ✅ Fix async/await in call_tool()
2. ✅ Fix method name routing (add await keywords)
3. ✅ Test existing 8 tools

### Phase 2: ADD MISSING TOOLS (Do Second)
1. ✅ Add `get-paper` routing
2. ✅ Add `list-papers` routing
3. ✅ Add `search-papers` routing
4. ✅ Add `upload-bibliography-batch` tool definition + routing

### Phase 3: EXPOSE HIDDEN HANDLERS (Do Third)
1. ✅ Add `get-quality-assessment` tool
2. ✅ Add `get-paper-structure` tool
3. ✅ Add `generate-slr-report` tool
4. ✅ Add `detect-remove-duplicates` tool

### Phase 4: INTEGRATION HANDLERS (Do Last)
1. ✅ Add `create-slr-project` tool
2. ✅ Add screening workflow tools
3. ✅ Add workflow guidance tools

---

## 💾 Implementation Checklist

### Quick Fixes (Can do now)

```python
# Fix 1: Update server.py call_tool() with await
# File: src/server.py, line ~308
if name == "upload-paper":
    result = await handler.handle_upload_paper(arguments)  # Add await!

# Fix 2: Add "get-paper" route
elif name == "get-paper":
    result = await handler.handle_get_paper(arguments)

# Fix 3: Add "list-papers" route
elif name == "list-papers":
    result = await handler.handle_list_papers(arguments)

# Fix 4: Add "search-papers" route
elif name == "search-papers":
    result = await handler.handle_search_papers(arguments)
```

### Missing Tool Definitions (Add to server.py list_tools)

```python
# Add to types.Tool list (~line 200):
types.Tool(
    name="get-paper",
    description="Retrieve a research paper by ID with full metadata",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "integer",
                "description": "ID of the paper to retrieve"
            }
        },
        "required": ["paper_id"]
    }
),
types.Tool(
    name="list-papers",
    description="List research papers with optional filtering",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 20},
            "offset": {"type": "integer", "default": 0},
            "filters": {"type": "object"}
        }
    }
),
# ... etc
```

---

## 📝 Testing Strategy

After fixes, test:

```bash
# Test 1: Upload paper
mcp call upload-paper \
  --file-path "test.pdf"

# Test 2: Get paper (currently broken)
mcp call get-paper \
  --paper-id 239

# Test 3: List papers (currently broken)
mcp call list-papers \
  --limit 10

# Test 4: Search papers (currently missing)
mcp call search-papers \
  --query "speech translation"
```

---

## 📊 Impact Assessment

**Current State**: 50% tools working partially
**After Fixes**: 95%+ tools working fully

**Users Currently Unable To**:
- ❌ Get paper details
- ❌ List papers
- ❌ Search papers
- ❌ Generate reports
- ❌ Manage duplicates
- ❌ Create projects
- ❌ Batch import bibliography

**Users Will Be Able To** (After Fixes):
- ✅ Full CRUD operations on papers
- ✅ Complete workflow automation
- ✅ All SLR operations via MCP

---

## 🚀 Conclusion

**Missing Features Found**: 8 major gaps
**Critical Issues**: 2 (async, routing)
**Estimated Fix Time**: 1-2 hours
**Impact**: Enables 9 additional tools (8 more than available now)

**Recommendation**: Fix Phase 1 & 2 today to unlock 85% of functionality.

---

**Status**: Analysis Complete  
**Severity**: 🔴 HIGH - Many tools are broken/missing  
**Action Required**: YES - Please fix async/routing issues ASAP
