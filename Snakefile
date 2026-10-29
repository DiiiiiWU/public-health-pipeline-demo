# Snakemake manages dependencies and execution; pipeline.py processes the data.
# "all" is the default target, not an additional data-transformation step.
rule all:
    input:
        "output/summary.csv"  # Final file that makes the workflow complete.

rule validate:
    input:
        "data/reports.csv"  # Raw data must exist before validation starts.
    output:
        "output/validated.csv"  # A successful check produces this file.
    shell:
        "python3 pipeline.py validate"  # Run Stage 1's Python function.

rule deduplicate:
    input:
        "output/validated.csv"  # Wait for Stage 1 to finish successfully.
    output:
        "output/unique.csv"  # Cleaned event-level dataset.
    shell:
        "python3 pipeline.py deduplicate"  # Run Stage 2.

rule aggregate:
    input:
        "output/unique.csv"  # Wait for Stage 2 to finish successfully.
    output:
        "output/summary.csv"  # Final metric, one row in a CSV file.
    shell:
        "python3 pipeline.py aggregate"  # Run Stage 3.
