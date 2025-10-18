# Runtime Data Directory

This directory contains runtime data files for the SLR server.

## Subdirectories

### `projects/`
Contains project-specific data and screening information organized by project.

**Structure**:
```
projects/
├── project-1/
│   ├── papers/
│   │   ├── screening/
│   │   ├── included/
│   │   └── excluded/
│   └── metadata.json
├── project-2/
│   └── ...
```

**Purpose**:
- Organize papers by project
- Track screening decisions per project
- Store project-specific metadata

---

### `papers/`
Contains uploaded research papers and their metadata.

**Structure**:
```
papers/
├── pdf/
│   ├── paper-1.pdf
│   ├── paper-2.pdf
│   └── ...
├── metadata/
│   ├── paper-1.json
│   ├── paper-2.json
│   └── ...
└── chunks/
    ├── paper-1-chunks.json
    ├── paper-2-chunks.json
    └── ...
```

**Purpose**:
- Store uploaded paper files
- Store extracted metadata
- Store document chunks for analysis

---

## Important Notes

⚠️ **Do Not Commit to Git**
- These directories are generated at runtime
- Add to `.gitignore` to prevent accidental commits
- They are excluded from version control

✅ **Backup Considerations**
- Regular backups recommended for `papers/` directory
- Project data should be backed up before deployment
- Consider archiving old projects periodically

🔄 **Migration**
- Data directory location can be changed
- Update paths in configuration if moving
- Ensure database reflects new paths

---

## Directory Usage Examples

### Creating a Project
```python
# Project data created automatically when project created
# Located in: data/projects/{project_name}/
```

### Uploading Papers
```python
# Papers stored in: data/papers/pdf/
# Metadata stored in: data/papers/metadata/
```

### Accessing Data
```bash
# View all projects
ls data/projects/

# View papers in project
ls data/projects/{project_name}/papers/

# View uploaded papers
ls data/papers/pdf/
```

---

## Maintenance

### Cleaning Old Data
```bash
# Remove old project (use with caution)
rm -rf data/projects/{old_project_name}

# Archive papers
tar -czf papers-backup.tar.gz data/papers/
```

### Verifying Data Integrity
```bash
# Check directory structure
tree data/

# Count papers
find data/papers/pdf -type f | wc -l

# List projects
ls -la data/projects/
```

