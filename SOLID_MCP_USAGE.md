# SOLID MCP Server - Troubleshooting & Usage Guide

## ✅ Server Status: WORKING

The SOLID MCP server is fully functional and ready to use with VS Code Copilot!

## Configuration Verified

Your `.vscode/mcp.json` is correctly configured:

```json
{
  "servers": {
    "solid": {
      "command": "python",
      "args": [
        "solid-server/src/main.py",
        "--project-root",
        "${workspaceFolder}"
      ],
      "cwd": "C:/github/mcp-servers",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

## How to Use with VS Code Copilot

### Step 1: Reload VS Code Window
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type "Reload Window"
3. Select **Developer: Reload Window**

### Step 2: Verify MCP Server is Running
1. Open Output panel: `View → Output` or `Ctrl+Shift+U`
2. From the dropdown, select **MCP** or **MCP Servers**
3. You should see:
   ```
   Starting SOLID Principles MCP Server with project root: ...
   Starting SOLID Principles MCP Server
   ```

### Step 3: Use the Tools via Copilot Chat

The server provides **6 SOLID analysis tools**:

#### 🔍 **solid-check-file**
Analyze a single Python file for SOLID violations.

**Example prompts:**
- "Check solid-server/src/main.py for SOLID violations"
- "Analyze the mcp_handler.py file for SOLID principles"
- "Check only SRP violations in server.py"

#### 📂 **solid-check-directory**
Analyze all Python files in a directory.

**Example prompts:**
- "Analyze the solid-server directory for SOLID violations"
- "Check all files in src/ for SOLID compliance"
- "Scan the whisper-server for SOLID issues"

#### 📊 **solid-generate-report**
Generate comprehensive reports in text, JSON, or Markdown format.

**Example prompts:**
- "Generate a SOLID report for solid-server in markdown format"
- "Create a JSON report of SOLID violations for the src directory"
- "Generate a report with improvement suggestions"

#### 📖 **solid-explain-principle**
Get detailed explanations with examples for each SOLID principle.

**Example prompts:**
- "Explain the Single Responsibility Principle"
- "What is the Dependency Inversion Principle? Show examples"
- "Explain LSP with code examples"

#### 🎯 **solid-check-score**
Get SOLID compliance scores for files or directories.

**Example prompts:**
- "What's the SOLID score for solid-server?"
- "Check the compliance score for mcp_handler.py"
- "Show me the overall SOLID score"

#### 📋 **solid-list-violations**
List all violations with filtering options.

**Example prompts:**
- "List all DIP violations in the project"
- "Show high severity SOLID violations only"
- "List SRP violations in the server directory"

## Available Resources

The server also provides 2 MCP resources:

1. **solid://principles** - Comprehensive SOLID principles guide
2. **solid://current-score** - Overall project SOLID score

## Testing the Server

### Quick Test (Test Mode)
```bash
cd solid-server
python src/main.py --test
```

### Protocol Test (Verify MCP Communication)
```bash
cd c:/github/mcp-servers
python test_solid_mcp_protocol.py
```

## Common Issues & Solutions

### ❌ "Cannot access tools"
**Solution:** Reload VS Code window (`Ctrl+Shift+P` → Reload Window)

### ❌ "Server not found in MCP logs"
**Solution:** 
1. Check that `mcp` package is installed: `pip list | grep mcp`
2. If not installed: `pip install mcp>=0.1.0`
3. Reload VS Code

### ❌ "Python command not found"
**Solution:** 
1. Make sure Python is in your PATH
2. Or update `.vscode/mcp.json` to use full Python path:
   ```json
   "command": "C:/Users/YourUser/AppData/Local/Programs/Python/Python312/python.exe"
   ```

## Example Copilot Conversation

**You:** "Analyze the solid-server for SOLID violations"

**Copilot:** *Uses solid-check-directory tool*
```
SOLID Analysis Report: solid-server
Average Score: 41.4/100
...
```

**You:** "Explain the violations in mcp_handler.py"

**Copilot:** *Uses solid-check-file tool to analyze specific violations*

**You:** "What is the Single Responsibility Principle?"

**Copilot:** *Uses solid-explain-principle tool*

## Requirements

- Python 3.8+
- `mcp>=0.1.0` (installed ✅)
- `pydantic>=2.0.0` (installed ✅)

## Next Steps

1. **Reload VS Code** to activate the MCP server
2. Open **Copilot Chat** (`Ctrl+Shift+I` or click Copilot icon)
3. Try asking: *"Check the SOLID score for solid-server"*
4. The server will automatically be invoked! 🎉

---

**Server Version:** 1.0.0  
**Protocol:** MCP (Model Context Protocol)  
**Status:** ✅ Fully Operational
