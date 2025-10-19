# Step-by-Step Implementation Guide

## Objective
Integrate automatic documentation generation into your existing MCP server with minimal code changes.

## Prerequisites
✅ `screening_documentation.py` already created in `src/automation/`  
✅ Existing MCP server running with `screen-paper` tool  
✅ Access to modify `src/server.py`

---

## Implementation Steps

### Step 1: Add Import (Line 1-20 in server.py)

**Find this section:**
```python
# src/server.py - Top imports section
import asyncio
import logging
from pathlib import Path
from typing import Optional
```

**Add these imports:**
```python
# Add after existing imports
from src.automation.screening_documentation import (
    ScreeningDocumentationSystem,
    ScreeningDecision
)
```

**Full section should look like:**
```python
import asyncio
import logging
from pathlib import Path
from typing import Optional

from src.automation.screening_documentation import (
    ScreeningDocumentationSystem,
    ScreeningDecision
)
```

✅ **Check**: Imports added without conflicts

---

### Step 2: Initialize Documentation System (In __init__)

**Find this section:**
```python
class SLRMCPServer:
    def __init__(self, project_root: Optional[Path] = None):
        self.server = Server("slr-mcp-server")
        self.project_root = project_root or Path.cwd()
        # ... other initializations ...
        logger.info("SLR MCP Server initialized")
```

**Add after logger initialization:**
```python
        # Initialize automatic documentation system
        self.doc_system = ScreeningDocumentationSystem(
            project_root=self.project_root,
            project_name="real-time-translation-platform"
        )
        logger.info("Documentation system initialized")
```

**Full section should look like:**
```python
class SLRMCPServer:
    def __init__(self, project_root: Optional[Path] = None):
        self.server = Server("slr-mcp-server")
        self.project_root = project_root or Path.cwd()
        # ... other initializations ...
        logger.info("SLR MCP Server initialized")
        
        # Initialize automatic documentation system
        self.doc_system = ScreeningDocumentationSystem(
            project_root=self.project_root,
            project_name="real-time-translation-platform"
        )
        logger.info("Documentation system initialized")
```

✅ **Check**: Documentation system initialized in __init__

---

### Step 3: Wrap screen-paper Handler

**Find the current screen_paper handler:**
```python
@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    """Handle tool calls"""
    
    if name == "screen-paper":
        # CURRENT IMPLEMENTATION - Find this section
        project_id = arguments.get("project_id")
        paper_id = arguments.get("paper_id")
        reviewer_id = arguments.get("reviewer_id")
        # ... existing code ...
        
        return [TextContent(type="text", text=f"✅ Screening recorded...")]
```

**Replace with this enhanced version:**
```python
@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    """Handle tool calls"""
    
    if name == "screen-paper":
        return await self._handle_screen_paper_with_docs(arguments)
    
    # ... other tool handlers ...
```

**Add this new method to the class (somewhere after handle_call_tool):**
```python
    async def _handle_screen_paper_with_docs(self, arguments: dict) -> list:
        """
        Handle screen_paper with automatic documentation generation
        
        Automatically logs decisions to JSON, updates CSV, generates
        markdown decision records, and triggers daily reports.
        """
        try:
            # Extract parameters
            project_id = arguments.get("project_id")
            paper_id = arguments.get("paper_id")
            reviewer_id = arguments.get("reviewer_id")
            decision = arguments.get("decision")
            confidence = arguments.get("confidence_level", 0.5)
            reason = arguments.get("reason", "")
            stage = arguments.get("stage", "title_abstract")
            exclusion_criteria = arguments.get("exclusion_criteria", [])
            
            logger.info(f"Processing screen_paper: Paper {paper_id}, {reviewer_id}, {decision}")
            
            # Get paper metadata for documentation
            paper = self.service.document_service.get_paper(paper_id)
            
            # 1. Record in MCP database (existing functionality)
            screening_result = self.service.record_screening_decision(
                project_id=project_id,
                paper_id=paper_id,
                reviewer_id=reviewer_id,
                stage=stage,
                decision=decision,
                confidence_level=confidence,
                reason=reason,
                exclusion_criteria=exclusion_criteria
            )
            
            # 2. Create decision object for auto-documentation
            screening_decision = ScreeningDecision(
                paper_id=paper_id,
                reviewer_id=reviewer_id,
                decision=decision,
                confidence_level=confidence,
                reason=reason,
                exclusion_criteria=exclusion_criteria if exclusion_criteria else None,
                stage=stage
            )
            
            # 3. **AUTOMATIC**: Trigger documentation generation
            #    This creates JSON logs, updates CSV, generates markdown files
            #    All handled asynchronously
            self.doc_system.log_paper_decision(
                decision=screening_decision,
                paper_title=paper.title,
                paper_year=paper.publication_year
            )
            
            logger.info(f"Documentation generated for paper {paper_id}")
            
            # 4. Return success response
            return [TextContent(
                type="text",
                text=f"""✅ Screening recorded and documented

Decision ID: {screening_result['id']}
Paper: {paper_id}
Reviewer: {reviewer_id}
Decision: {decision.upper()}
Confidence: {confidence}

📝 Auto-Generated Files:
  - logs/screening_{paper_id}_{reviewer_id}.json
  - screening_log.json (updated)
  - screening_progress.csv (updated)

Ready for next screening!"""
            )]
            
        except Exception as e:
            logger.error(f"Error in screen_paper with docs: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"❌ Error recording screening: {str(e)}"
            )]
```

✅ **Check**: New handler method added and integrated

---

### Step 4: (Optional) Add Daily Report Generation

**Add this new tool to your tools list (in get_tools method):**
```python
Tool(
    name="generate-daily-report",
    description="Generate daily screening summary report with metrics",
    inputSchema={
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Report date (e.g., 'OCT19'). If not provided, uses today's date."
            }
        }
    }
)
```

**Add this handler in handle_call_tool:**
```python
    if name == "generate-daily-report":
        date = arguments.get("date")
        try:
            report_path = self.doc_system.generate_daily_report(date=date)
            return [TextContent(
                type="text",
                text=f"✅ Daily report generated: {report_path}"
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Error: {str(e)}")]
```

✅ **Check**: Optional daily report tool added

---

## Verification Checklist

After implementing above changes:

- [ ] Import added without syntax errors
- [ ] Documentation system initialized in `__init__`
- [ ] New method `_handle_screen_paper_with_docs` added
- [ ] Handler wrapped in `handle_call_tool`
- [ ] Code compiles without errors
- [ ] MCP server starts successfully

---

## Testing the Integration

### Test 1: Single Decision
```bash
# Call screen_paper tool
curl -X POST http://localhost:3001/tools/screen-paper \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "paper_id": 232,
    "reviewer_id": "reviewer1",
    "stage": "title_abstract",
    "decision": "include",
    "confidence_level": 0.85,
    "reason": "Test decision"
  }'

# Expected: ✅ Decision recorded and documented
# Check: ls screening/title-abstract/logs/
#        → screening_232_reviewer1.json should exist ✅
```

### Test 2: Agreement Detection
```bash
# Call for second reviewer - same paper, same decision
curl -X POST http://localhost:3001/tools/screen-paper \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "paper_id": 232,
    "reviewer_id": "reviewer2",
    "stage": "title_abstract",
    "decision": "include",
    "confidence_level": 0.90,
    "reason": "Test agreement"
  }'

# Expected: ✅ AGREEMENT DETECTED
# Check: ls screening/title-abstract/decisions/
#        → 232_decision_record.md should exist ✅
```

### Test 3: Daily Report
```bash
# Generate daily report
curl -X POST http://localhost:3001/tools/generate-daily-report \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected: ✅ Daily report generated
# Check: ls screening/title-abstract/reports/
#        → daily_summary_[DATE].md should exist ✅
```

---

## Common Issues & Solutions

### Issue: Import Error
```
ModuleNotFoundError: No module named 'src.automation'
```
**Solution**: Ensure `screening_documentation.py` exists at `src/automation/screening_documentation.py`

### Issue: AttributeError on self.doc_system
```
AttributeError: 'SLRMCPServer' object has no attribute 'doc_system'
```
**Solution**: Verify `__init__` includes documentation system initialization

### Issue: Files not being created
```
✅ Decision recorded but no files generated
```
**Solution**: Check folder structure:
```bash
mkdir -p screening/title-abstract/logs
mkdir -p screening/title-abstract/decisions
mkdir -p screening/title-abstract/reports
```

### Issue: Logging not working
```
No log entries for documentation system
```
**Solution**: Add explicit logging after initialization:
```python
logger.info(f"Documentation system root: {self.doc_system.screening_root}")
```

---

## Expected Output Structure

After successful implementation, you should see:

```
real-time-translation-platform/screening/title-abstract/
├── logs/
│   ├── screening_232_reviewer1.json ✅
│   └── ... (more logs)
├── decisions/
│   ├── 232_decision_record.md ✅ (when both reviewers complete)
│   └── ... (more decisions)
├── reports/
│   ├── daily_summary_OCT19.md ✅ (after generate-daily-report)
│   └── ... (more reports)
├── screening_log.json ✅
├── screening_progress.csv ✅
└── summaries/
    ├── current_metrics.json ✅
    └── screening_stats.json ✅
```

---

## Success Criteria

✅ **Implementation Complete When:**
1. Code added to `server.py` without errors
2. MCP server starts successfully
3. `screen-paper` tool still works (returns success)
4. New JSON/CSV files created after each tool call
5. Decision markdown files created when both reviewers complete
6. Daily reports generated on demand

✅ **Ready for Full Screening When:**
1. All 5 success criteria met
2. Files created in correct locations
3. File contents are properly formatted
4. No errors in server logs
5. Metrics calculated correctly

---

## Next: Start Full Screening

Once implementation verified:

1. **Get list of papers to screen**
   ```
   mcp_slr-server_list_papers(limit=10)
   ```

2. **For each paper, both reviewers decide**
   ```
   mcp_slr-server_screen_paper(paper_id, reviewer1, decision, ...)
   mcp_slr-server_screen_paper(paper_id, reviewer2, decision, ...)
   ```

3. **Watch documentation auto-generate**
   - logs created per decision
   - decisions marked when agreement/conflict
   - daily reports generated

4. **Monitor progress**
   ```
   mcp_slr-server_get_slr_progress(project_id=1)
   ```

---

**Implementation Time**: ~15-20 minutes  
**Testing Time**: ~10 minutes  
**Ready to screen**: ~30 minutes total  

**Let's automate your screening workflow!** 🚀
