# pymri — Architecture & Codebase Overview

## Purpose

pymri is a Python framework for MRI data analysis. It does not perform computations directly: it orchestrates external tools (FSL via shell commands, SPM via MATLAB batch files) and manages the surrounding infrastructure — file system layout, subject data, preprocessing pipelines, and group-level statistics.

Consumer projects live outside this folder (in a separate `pymri_projects/` tree). They import pymri classes, instantiate an `MRIProject` + `MRIGlobal`, load subjects, and call methods.

---

## Top-Level Structure

```
pymri/
├── project/
│   ├── Project.py      # Base project class: data loading, subject lists, query helpers
│   ├── MRIProject.py   # MRI project: extends Project, adds subjects, file system, orchestration
│   ├── DataProject.py  # Data-only project: extends Project, no MRI tools required
│   ├── MRIGlobal.py    # Environment configuration (FSL, SPM, paths)
│   └── Global.py       # Environment configuration (generic)
├── subject/            # Per-subject MRI processing
├── group/              # Group-level analyses (SPM, FSL)
├── models/             # FSL/SPM model builders
├── data/               # Subject data (Excel/CSV), DB classes
├── myutility/          # Low-level utilities (images, FSL wrappers, MATLAB)
├── resources/          # SPM batch templates (.m), standard images
└── local.settings      # Machine-local paths (not committed)
```

---

## Configuration Layer (`Global` Hierarchy)

### `Global` (Base Class)
Environment configuration for framework. Implements safe property access without requiring MRI tools or `local.settings`. Provides:
- `framework_dir` — path to pymri codebase
- `project_scripts_dir` — path to consumer script projects
- `ignore_warnings` — bool flag for warning suppression
- `_safe_get_setting(data_dict, key, default=None)` — helper for safe config reading

### `MRIGlobal(Global)` (Extends Global)
MRI-specific configuration. Reads `local.settings` safely and resolves all tool paths:
- FSL directory, FSL derivatives (BET, FLIRT, FNIRT, topup, etc.)
- SPM directory and version
- CAT (Computational Anatomy Toolbox) version and options
- ICA-AROMA script path
- Standard MNI templates (2mm, 4mm)
- DTI xtract labels and coordinates
- Matlab engine configuration

Implements `check_paths(full_check=True)` to validate MRI tool directories exist (skipped if `full_check=False`). Every MRI-based class receives an `MRIGlobal` instance at construction.

---

## Project Layer (`Project` Hierarchy)

### `Project` (Base Class)
Generic project management. Handles `SubjectsData` dataframe and named subject lists (no MRI tools required). Provides:
- `dir` — project root folder
- `subjects_dir` — `project_dir/subjects`
- `subjects_lists` — named lists from `subjects_lists.json`
- `data` — a `SubjectsData` instance
- `load_data()`, `validate_data()` — data file discovery with search path support (internal helper: `_resolve_data_path()`)
- `_get_subjects_labels(group_label)` — private helper, resolves group label → list of subject labels
- `get_subjects(group_or_subjlabels, sess_ids, must_exist)` → `SubjectsList` — **universal entry point**: converts str/List[str] → SubjectsList with Subject instances
- `get_subjects_values_by_cols(subjects, columns, ...)`, `get_filtered_column(subjects, column, ...)`, `get_subjects_datarows(subjects, ...)` — subject queries accepting only `SubjectsList`

`subjects_lists_file` defaults to `proj_dir/subjects_lists.json`. Subclasses may override it before calling `super().__init__()`.

### `DataProject(Project)` (Extends Project)
Lightweight variant for data-only analysis (no MRI tools). Adds:
- `input_data_dir` — `proj_dir/input_data/`
- `output_data_dir` — `proj_dir/output_data/`
- `subjects_lists_file` and data file both live in `proj_dir`

Used by analysis scripts needing only demographic/clinical data (e.g. R-compatible exports, statistical covariates).

### `MRIProject(Project)` (Extends Project)
The main object for an MRI study. Overrides Project to add MRI infrastructure:
- `globaldata` — reference to `MRIGlobal` (required, not optional)
- `subjects_dir`, `group_analysis_dir`, `script_dir`, `vbm_dir`, `tbss_dir`, etc. — MRI filesystem layout
- `subjects` — loaded list of `SubjectMRI` instances
- `subjects_lists_file` — lives in `script_dir` (outside the project folder, in `project_scripts_dir/name/`)
- `load_data()` searches for data file in `script_dir`
- `get_subjects(group_or_subjlabels, sess_ids, must_exist)` → `SubjectsList` — **override**: calls parent, then casts each Subject → SubjectMRI
- All query methods accept only `SubjectsList` (inherited from parent with MRI-specific filtering via `subjects2sids()`)

Key methods: `load_subjects()`, `get_subjects()` (override), `get_subject_session()`, `subjects2sids()`, `sids2subjects()`, `adapt_batch_files()`, `run_subjects_methods()`.

---

## Subject Layer (`subject/`)

### `Subject` (Base Class)
Generic subject representation. Atomic unit of research (label + session), independent of MRI. Provides:
- `label` — subject identifier
- `sessid` — session number (default: 1)
- `project` — reference to parent Project
- `@property dir` — returns `project.subjects_dir / label / sessid`
- `@property exist` — bool checking if directory exists on filesystem
- `is_equal(other: Subject) → bool` — compares label and sessid only
- `is_in(subjects: List[Subject]) → bool` — checks membership
- `get_properties(sessid: int) → Subject` — creates copy with different session

No MRI dependencies. Works for any research domain.

### `SubjectMRI(Subject)` (Extends Subject)
MRI-specific subject implementation. Inherits all Subject functionality, adds:
- `global_config` — reference to `MRIGlobal` for tool access
- `@property dir` — overridden to use MRI session format ("s1", "s2", etc.)
- MRI directory properties: `t1_dir`, `dti_dir`, `rs_dir`, `fmri_dir`, `t2_dir`, `roi_dir`, etc.
- Image path properties: `t1_data`, `dti_data`, `rs_data`, `rs_pa_data`, `fmri_data`, `t2_data`, etc.
- Sequence checking: `hasT1`, `hasRS`, `hasDTI`, `hasT2`, `hasFMRI()`, `hasSeq(type, images_labels)` → bool

#### Sub-objects (MRI processing modules)
Each `SubjectMRI` owns four sub-objects that group related processing:

| Sub-object | Class | Responsibility |
|---|---|---|
| `subject.mpr` | `SubjectMpr` | T1 preprocessing: bias correction, BET, SPM segmentation, CAT cortical thickness |
| `subject.epi` | `SubjectEpi` | EPI preprocessing: slice timing, topup, motion correction, nuisance regression, fMRI first-level |
| `subject.dti` | `SubjectDti` | DTI pipeline: eddy correction, dtifit, bedpostX, probtrackX, xtract |
| `subject.transform` | `SubjectTransforms` | All cross-space registrations (linear + nonlinear): T1↔std, T1↔rs, T1↔DTI, etc. |

#### Processing methods
- `wellcome()` — main preprocessing orchestration (calls mpr, epi, dti methods in sequence)
- `check_images()` — validates required images exist
- `create_file_system()` — initializes MRI directory structure
- `rename()` — renames subject label (updates filesystem)
- `set_properties(sess, rollback=True)` — returns deep-copy with paths rewritten for different session (leaves `self` unchanged if `rollback=True`)

### Filesystem convention
```
subjects/
  LABEL/
    s1/
      mpr/        ← T1, BET output, SPM/CAT dirs
      resting/    ← rs-fMRI, AROMA, nuisance
      fmri/       ← task fMRI
      dti/        ← DTI, bedpostX, probtrackX, xtract
      t2/
      roi/
        reg_t1/   ← T1-space ROIs and transform matrices
        reg_rs/
        reg_dti/
        reg_std/
        reg_std4/
        ...
```

---

## Group Analysis Layer (`group/`)

| Class | Role |
|---|---|
| `GroupAnalysis` | FSL group analyses: TBSS (FA + alternatives), VBM template creation, connectivity matrix preparation (DSI/CONN→NBS), xtract group export, randomise |
| `SPMModels` | SPM second-level factorial designs: one/two-sample t-test, one/two-way ANOVA, multiple regression. Selects correct SPM template, fills placeholders, calls MATLAB |
| `SPMContrasts` | Generates MATLAB contrast strings (T/F contrasts, 1-way ANOVA pairwise contrasts, multiple-regression auto-contrasts) |
| `SPMCovariates` | Appends covariate/regressor strings to SPM batch files |
| `SPMPostModel` | Post-estimation batch: contrast definition after model estimation |
| `SPMResults` | SPM results reporting |
| `SPMStatsUtils` | Helpers: compose image list strings per design type, handle explicit masks, global calculation |
| `SPMConstants` | Integer constants for stat types (MULTREGR, OSTT, TSTT, OWA, TWA) and analysis types (VBM_DARTEL, CAT, FMRI) |

For SPM analyses the pattern is: copy an `.m` template from `resources/templates/spm/`, apply `sed_inplace()` to replace `<PLACEHOLDER>` tags with real paths/values, then call `call_matlab_spmbatch()`.
For FSL analyses the pattern is: create a command string with the fsl executable name and all the required parameters, and run it in console.

---

## Models Layer (`models/`)

| Class | Role |
|---|---|
| `FSLModels` | Reads/writes FSL GLM `.mat`/`.con` files, queries contrast counts and data points |
| `FSLConFile` | Low-level FSL contrast file parser |
| `SPMModels` | (see group section) |
| `ConnModels` | Connectivity model helpers |
| `NBSModels` | NBS (Network-Based Statistics) model helpers |

---

## Utility Layer (`myutility/`)

### `images/Image`
`Image` extends `str`. A path is an `Image` — you can pass it anywhere a string is expected, but it also carries:
- `exist`, `uexist`, `cexist` — checks for `.nii`, `.nii.gz`, `.hdr/.img`, `.mgz`, `.gii`
- `upath`/`cpath` — uncompressed/compressed variants
- `cp()`, `mv()`, `rm()`, `compress()`, `unzip()`
- `nvols`, `nslices`, `TR` — via `fslval`/`fslnvols`
- `read_header()` — via `fslhd -x` (returns a dict)
- `quick_smooth()`, `get_nth_volume()`, `filter_volumes()`, `imsplit()`

### `images/Images`
A list of `Image` with batch operations.

### `myfsl/`
- `rrun()` — the main FSL command runner (subprocess, returns stdout, raises on error)
- `run()`, `runpipe()`, `runsystem()` — variants (pipe, os.system, etc.)
- `fsl_switcher` — activates a specific FSL version by manipulating env variables

### `mymatlab.py`
- `start_matlab()` — connects to an existing MATLAB session or starts a new one via `matlab.engine`
- `call_matlab_spmbatch(func, paths)` — the main SPM entry point: adds paths, calls the batch `.m` function, quits
- `call_matlab_function()` / `call_matlab_function_noret()` — general MATLAB function calls with/without return value

### Other utilities
- `fileutilities.py` — `sed_inplace()` (in-place string replacement in `.m` files), `compress()`/`gunzip()`, `write_text_file()`, `extractall_zip()`
- `exceptions.py` — custom exceptions: `DataFileException`, `SubjectExistException`, `SubjectListException`, `NotExistingImageException`
- `SubjectTracts` / `Tract` — DTI tract results containers (label + per-metric values)

---

## Data Layer (`data/`)

There are two systems built on top of each other.

### System A — General subject data (used by MRI pipelines)

```
SID
  label: str, session: int, id: int (DataFrame row index)

SIDList(list[SID])
  .labels, .sessions, .ids
  .is_in(), .contains(), .are_equal(), .append_novel()

SubjectsData
  .df: DataFrame  (requires columns: subj, session)
  .subjects → SIDList
  .filter_subjects(labels, sess_ids, conditions) → SIDList
  .get_sid(label, sess) → SID
  .select_df(sids, validcols) → DataFrame
  .get_subject_col_value(sid, col) → Any
  .get_subjects_column(sids, col) → List[Any]
  .set_subj_session_value(sid, col, value)
  .add_row(), .add_column(), .add_sd(), .remove_subjects(), .rename_subjects()
```

`FilterValues` is a condition object used in `filter_subjects()`:
```python
FilterValues("group", "==", "TD")
FilterValues("mri_code", "exist", None)
FilterValues("age", "<>", (18, 65))
```

`SubjectsData` is the single-sheet building block. `Project.data` is one instance of it.

### System B — Multi-sheet Excel database (specific to the BayesDB project)

Built on top of System A, adds schema-driven multi-sheet management:

```
Sheets(dict)
  keys: sheet names → SubjectsData values
  .main → main SubjectsData
  .all_subjects → union SIDList across all sheets
  .is_consistent → bool (same subjects in every sheet)

MSHDB
  .sheets: Sheets
  .schema_file: JSON that defines sheet names, unique columns, dates, rounding
  .main → SubjectsData of main sheet
  .subjects → SIDList from main sheet
  load(xlsx/GDriveSheet/Sheets)
  save(xlsx/GDriveSheet)
  get_sheet_sd(name) → SubjectsData
  select_df(subjs, {sheet: [cols]}) → DataFrame
  add_new_subjects(), remove_subjects(), rename_subjects()
  make_consistent_to(mainDB)  ← ensures all sheets have rows for all subjects

BayesDB(MSHDB)
  Concrete database for the "Bayes" psychiatric study.
  Adds session-aware unique key [subj, session, group].
  Extra methods:
    get_groups(sids), mri_labels(), blood_labels(), bisection_labels()
    calc_flags()  ← derives binary flags (mri, oa, nk, t, m, b, ...) from sheet cells
    sort(), compare_db()
    is_consistent → validates subjects + group columns across all sheets

GDriveSheet
  Wraps gspread to read/write a Google Spreadsheet as a Sheets object.

BayesImporter
  Reads a per-subject Excel form (EteroDB format), parses cells by position
  according to an import schema JSON, and produces a BayesDB object.
  Two modes: full etero form (__set_main) and lightweight auto form (__set_main_auto).

LimeAutoImporter, VolBrainImporter
  Specialized importers for LimeSurvey exports and VolBrain morphometry files.
```

---

## Data Flow — Typical MRI Project

```
MRIGlobal("6.0.4")
  └─ reads local.settings → resolves FSL, SPM, template paths

MRIProject("/data/MRI/projects/MyStudy", globaldata)
  └─ reads subjects_lists.json (from script_dir)
  └─ loads data.xlsx → SubjectsData

project.load_subjects("controls", sess_ids=[1])
  └─ creates SubjectsList, each with .mpr/.epi/.dti/.transform

# Preprocessing
for subj in project.subjects:
    subj.mpr.prebet(...)         # fslmaths, bet, fnirt (FSL)
    subj.mpr.bet(...)
    subj.mpr.spm_segment(...)    # writes+runs SPM batch .m (MATLAB)
    subj.transform.transform_mpr(...)  # flirt, fnirt (FSL)
    subj.epi.topup_corrections(...)    # topup, applytopup (FSL)
    subj.dti.eddy(...)                 # eddy_openmp (FSL)
    subj.dti.fit(...)                  # dtifit (FSL)

# Group analysis
ga = GroupAnalysis(project)
ga.tbss_run_fa(project.subjects, "population")

spm = SPMModels(project)
spm.batchrun_group_stats(
    root_outdir = project.vbm_dir,
    stat_type   = SPMConstants.TSTT,
    anal_type   = SPMConstants.VBM_DARTEL,
    anal_name   = "controls_vs_patients",
    groups_instances = [controls, patients],
    covs = [Regressor("age"), Regressor("gender")]
)
```
