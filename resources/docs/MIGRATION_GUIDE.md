# Subject Loading Migration Guide

## Overview

The pymri framework has been refactored to auto-load subjects at project initialization.
The deprecated `load_subjects()` method has been replaced with the modern `get_subjects()` API.

## Pattern Changes

### Old Pattern (DEPRECATED - do not use)
```python
# Deprecated - will be removed in future versions
subjects = project.load_subjects("group_label", [SESS_ID])
subjects = project.load_subjects(["0001", "0002"], [SESS_ID])
```

### New Pattern - Single Project Analysis
```python
# Get subjects from a group label
subjects = project.get_subjects("group_label", sess_ids=[SESS_ID])

# Get subjects from explicit labels
subjects = project.get_subjects(["0001", "0002"], sess_ids=[SESS_ID])

# Get all subjects in the project
# Option 1: specify all sessions explicitly
subjects = project.get_subjects(project.subjects_labels, sess_ids=[1])

# Option 2: auto-detect all available sessions
all_subjects = project.subjects  # read-only property, auto-populated from excel

# Run methods on subjects
project.run_subjects_methods("epi", "spm_fmri_preprocessing", kwparams, ncore=num_cpu, subjects=subjects)

# Or use all subjects (omit subjects parameter)
project.run_subjects_methods("epi", "spm_fmri_preprocessing", kwparams, ncore=num_cpu)
```

### New Pattern - Cross-Project Analysis

For analyses combining subjects from multiple projects, manually build a SubjectsList:

```python
from subject.SubjectsList import SubjectsList

# Load data from multiple projects
ctrl_project = MRIProject(ctrl_proj_dir, globaldata)
pat_project = MRIProject(pat_proj_dir, globaldata)

# Get subjects from each project
ctrl_subjects = ctrl_project.get_subjects("controls", sess_ids=[SESS_ID])
pat_subjects = pat_project.get_subjects("patients", sess_ids=[SESS_ID])

# Combine into single list for cross-project analysis
all_subjects = SubjectsList()
all_subjects.extend(ctrl_subjects)
all_subjects.extend(pat_subjects)

# Each subject reads data from its own project
# (via subj.sid resolved in subj.project.data)
group_analysis.create_vbm_spm_template_normalize("population_name", all_subjects)
```

## Key Concepts

### Subject.sid - Auto-Contained SID

Each Subject instance now auto-contains its `sid` (Subject ID) resolved in its own `project.data`:
```python
subj = subjects[0]
# Each subject automatically reads its data from its own project
# Cross-project analysis works seamlessly without shared excel files
value = subj.get_col_value("age")  # reads from subj.project.data
```

### Subject.project - Reference to Parent Project

Every Subject knows its parent project:
```python
for subj in all_subjects:  # cross-project list
    # Each subject reads from its own project
    print(f"{subj.label} belongs to {subj.project.folder}")
```

## Migration Checklist

- [ ] Replace `project.load_subjects(...)` with `project.get_subjects(..., sess_ids=[...])`
- [ ] Remove any `subjects = project.load_subjects()` calls with implicit defaults
- [ ] For cross-project analysis, use explicit `SubjectsList.extend()` to combine subjects
- [ ] Verify `sess_ids` parameter is explicit (don't rely on default behavior)
- [ ] Test that `subject.get_col_value()` reads from correct project in cross-project analysis

## Examples

See `pymri/resources/examples/` for complete working examples:
- `subject/subjects_fmri.py` - Single-project fMRI preprocessing
- `subject/import_subjects.py` - Subject data import workflow  
- `group/xprojects_group_analysis.py` - Cross-project group analysis

## Deprecation Timeline

- **Current**: `load_subjects()` still works but emits `DeprecationWarning`
- **Future versions**: `load_subjects()` will be removed entirely
