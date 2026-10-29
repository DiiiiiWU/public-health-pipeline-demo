# A tiny public-health data pipeline: Python + Snakemake

**A classroom companion to “Data Processing Pipeline Development.”**  
Run a three-task workflow, see a validation failure, and learn why workflow managers can reuse completed outputs. **No real patient information is included.**

> **Important:** This is a teaching example, not a clinical or public-health surveillance system. It counts **distinct positive test events**, *not confirmed COVID-19 cases*. It assumes `test_id` is globally unique for each test event, and that two reports with the same ID and identical hospital/result describe the same event. Real systems need validated identifiers, reporting completeness checks, clinical case definitions, security, and much more.

## 1. The idea in 20 seconds

```text
hospital reports (data/reports.csv)
        |
        v
  validate stage        -> output/validated.csv
        |
        v
  deduplicate stage     -> output/unique.csv
        |
        v
  aggregate stage       -> output/summary.csv
```

The actual Python script is `pipeline.py` (with three subcommands). The **Snakefile** tells Snakemake which files each task requires and produces. The workflow runs **Validate → Deduplicate → Aggregate**; the broader design concerns **Define, Validate, Orchestrate** are *not* three sequential processing functions.

## 2. Quick start (Mac / Linux / Windows)

You need **Python 3** and **Snakemake**. The processing script itself needs **no third-party Python libraries**.

### Option A: run Python only (no installation beyond Python)

From the repository folder, run:

```bash
python3 pipeline.py validate
python3 pipeline.py deduplicate
python3 pipeline.py aggregate
cat output/summary.csv
```

Expected result:

```text
VALIDATE: 4 records passed the checks.
DEDUPLICATE: 4 reports -> 3 unique tests.
AGGREGATE: 2 distinct positive tests.
```

### Option B: let Snakemake run the workflow

For a reproducible installation, use **Miniforge / Conda or Mamba** and the supplied `environment.yml`:

```bash
conda env create -f environment.yml
conda activate public-health-pipeline-demo
```

Or use an existing compatible Snakemake installation (check with `snakemake --version`). On Windows, WSL is usually the simplest route for running the shell commands as written.

**Important:** If you already ran Option A, its output files exist. Remove them once to see a clean Snakemake run:

```bash
rm -rf output
snakemake -n -j 1           # Dry run: show the plan without executing
snakemake -j 1 -p           # Execute; print commands
cat output/summary.csv
```

On a clean run, Snakemake schedules `validate`, `deduplicate`, and `aggregate`, plus the target rule `all` (four rule jobs total, but **only three data-processing tasks**).

> `-j 1` allows one concurrent job. `-n` is a dry run. `-p` prints shell commands. A dry run after all files are up to date should say nothing needs to be done. If files were created outside Snakemake, missing provenance metadata warnings can appear; that is not the same as a data-validation error.

## 3. Challenge A — Make validation fail (beginner, 2 minutes)

**Goal:** See that invalid data do not silently flow into downstream calculations.

```bash
cp data/reports.csv data/reports.backup.csv
cp examples/invalid_result.csv data/reports.csv
snakemake -j 1 -p
```

Expected: Python raises `ValueError` because `Unknown` is not an allowed result. Snakemake reports a failed `validate` task; downstream tasks cannot be completed from the invalid input. **The command should exit with an error.**

Restore the original input, then rerun:

```bash
mv data/reports.backup.csv data/reports.csv
snakemake -j 1 -p
```

**Think:** Passing these checks does *not* establish that every hospital reported, that the event IDs are correct, or that a positive test equals a confirmed case.

## 4. Challenge B — Catch a conflicting duplicate (intermediate)

**Goal:** Understand why duplicate detection needs explicit event semantics.

```bash
cp data/reports.csv data/reports.backup.csv
cp examples/conflicting_duplicate.csv data/reports.csv
snakemake -j 1 -p
```

Here, test `103` appears twice with **different results**. The deduplication stage raises an error rather than silently choosing one. Restore:

```bash
mv data/reports.backup.csv data/reports.csv
snakemake -j 1 -p
```

**Think:** What additional identifiers or timestamps would a real hospital reporting system need?

## 5. Challenge C — Reuse upstream work (advanced, 2 minutes)

**Goal:** Show *dependency-aware incremental rerunning*, without breaking any Python code.

First finish a successful Snakemake run with the original data. Then:

```bash
rm output/unique.csv
snakemake -n -j 1     # Inspect the jobs Snakemake plans to run
snakemake -j 1 -p     # Recreate only necessary files
```

Expected: `validate` can be skipped if its output is still valid and up to date; Snakemake plans `deduplicate` and `aggregate` (plus the `all` target). Exact job counts and output wording vary by Snakemake version and metadata.

**Important distinction:** This demonstrates *rerunning tasks based on missing/stale outputs*, not resuming Python execution at the exact instruction where it crashed. A task that fails halfway through normally restarts from the beginning of that task.

## 6. Read the files

| File | Purpose |
|---|---|
| `data/reports.csv` | Four synthetic hospital reports (two copies of test 103) |
| `pipeline.py` | Three Python processing functions, commented line by line |
| `Snakefile` | Four rules specifying output targets and task dependencies |
| `examples/` | Two intentionally problematic input files for challenges |
| `tests/test_pipeline.py` | Automated tests for success and failure cases |
| `environment.yml` | Optional reproducible Snakemake environment |
| `output/` | Generated intermediate and final results; ignored by Git |

Run the tests without installing Snakemake:

```bash
python3 -m unittest discover -s tests -v
```

## 7. How this connects to the presentation

- **Define — What should the pipeline do?** Specify the input schema, expected metric, and input/output contract for each processing task.
- **Validate — Can we trust the number?** Check specified rules; reject malformed data and conflicting duplicates. These checks are necessary but not sufficient for real-world validity.
- **Orchestrate — How do we run and recover?** Snakemake tracks file dependencies, chooses tasks to execute, and records workflow runs. It does **not** decide whether your scientific assumptions are correct.

These are **three teaching perspectives synthesized from different literatures**, not an officially established named three-stage model.

## 8. References and further reading

- Wilson, G., et al. (2017). *Good enough practices in scientific computing*. PLOS Computational Biology. https://doi.org/10.1371/journal.pcbi.1005510
- Kahn, M. G., et al. (2016). *A harmonized data quality assessment terminology and framework for the secondary use of electronic health record data*. eGEMs. https://doi.org/10.13063/2327-9214.1244
- Mölder, F., et al. (2021). *Sustainable data analysis with Snakemake*. Nature Methods. https://doi.org/10.1038/s41592-021-01254-9
- Snakemake documentation: https://snakemake.readthedocs.io/
