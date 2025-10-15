# SLR Server - Clean Directory Structure

## 📁 Organized File Structure

```
slr-server/
├── 📂 src/                          # Core application code
│   ├── handlers/                    # MCP request handlers
│   ├── services/                    # Business logic services
│   ├── repositories/                # Data access layer
│   ├── models.py                    # Data models
│   ├── container.py                 # Dependency injection
│   └── main.py                      # Main server entry point
│
├── 📂 tests/                        # All test files
│   ├── test_complete_server.py      # Integration tests
│   ├── test_handlers.py             # Handler tests
│   ├── test_mcp_server.py           # MCP protocol tests
│   └── test_*.py                    # Other test files
│
├── 📂 scripts/                      # Utility scripts
│   ├── list_slr_tools.py           # Tool listing utility
│   ├── mcp_slr_client.py           # MCP client
│   ├── debug_server.py             # Debug utilities
│   └── slr_workflow.py             # Workflow helpers
│
├── 📂 config/                       # Configuration files
│   ├── claude_desktop_config.json  # Claude Desktop setup
│   └── docker_mcp_config.json      # Docker MCP config
│
├── 📂 deployment/                   # Deployment files
│   ├── docker-compose.yml          # Docker compose
│   ├── Dockerfile                  # Container definition
│   ├── deploy.sh                   # Unix deployment
│   └── deploy.ps1                  # Windows deployment
│
├── 📂 projects/                     # SLR project files
│   ├── slr_project_config.json     # Project configuration
│   ├── slr_project_plan.md         # Research plan
│   └── *.pdf                       # Source documents
│
├── 📂 docs/                         # Documentation
│   ├── MCP_USAGE_GUIDE.md          # MCP usage guide
│   ├── SLR_TOOLS_PRACTICAL_GUIDE.md # Tools guide
│   └── other documentation...
│
├── 📂 data/                         # Data directories
├── 📂 papers/                       # Paper storage
├── 📂 slr_outputs/                  # Generated outputs
├── 📂 htmlcov/                      # Coverage reports
│
├── 🐍 start_server.py               # Server startup
├── 📄 README.md                     # Main documentation
├── ⚙️ pyproject.toml                # Python project config
├── 📋 requirements.txt              # Dependencies
│
└── 🗄️ Database files (in use)
    ├── slr_corrected.db
    ├── slr_database.db
    └── slr_production.db
```

## ✅ Cleanup Summary

### 🗂️ **Organized:**
- **Tests** → `tests/` directory
- **Scripts** → `scripts/` directory  
- **Config** → `config/` directory
- **Deployment** → `deployment/` directory
- **Projects** → `projects/` directory

### 🗑️ **Removed Bloat:**
- Redundant documentation files
- Duplicate requirements files
- Placeholder implementation files
- Outdated priority lists

### 🎯 **Result:**
- **Clean structure** with logical file organization
- **Easy navigation** for developers and users
- **Separated concerns** (code, tests, config, deployment)
- **Project isolation** in dedicated directory

## 📋 Quick Access

- **Start server:** `python start_server.py`
- **List tools:** `python scripts/list_slr_tools.py`
- **Run tests:** `python -m pytest tests/`
- **Project config:** `projects/slr_project_config.json`

---
*Directory cleanup completed: October 15, 2025*