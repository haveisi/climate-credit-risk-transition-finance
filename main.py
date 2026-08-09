from pathlib import Path
import subprocess
import sys


# ==================================================
# PROJECT PATHS
# ==================================================

# main.py is located in the project root
PROJECT_ROOT = Path(__file__).resolve().parent

SRC_FOLDER = PROJECT_ROOT / "src"


# ==================================================
# PIPELINE SCRIPTS
# ==================================================

scripts = [
    "01_load_workbook.py",
    "02_extract_tables.py",
    "03_validate_inputs.py",
    "04_stress_model.py",
    "05_portfolio_summary.py",
    "06_qa_reconciliation.py",
    "07_export_results.py",
]


# ==================================================
# START PIPELINE
# ==================================================

print("=" * 100)
print("JPM CLIMATE CREDIT ANALYTICS PIPELINE")
print("=" * 100)

print("\nProject root:")
print(PROJECT_ROOT)

print("\nSource folder:")
print(SRC_FOLDER)


# ==================================================
# RUN EACH STAGE
# ==================================================

for script_name in scripts:

    script_path = SRC_FOLDER / script_name

    print("\n" + "=" * 100)
    print(f"RUNNING: {script_name}")
    print("=" * 100)

    print("Script path:")
    print(script_path)

    # Check that script exists
    if not script_path.exists():
        print(f"\nERROR: Script not found: {script_path}")
        sys.exit(1)

    # Run script using same Python environment
    result = subprocess.run(
        [sys.executable, str(script_path)]
    )

    # Stop pipeline if script fails
    if result.returncode != 0:

        print(
            f"\nPIPELINE FAILED AT: {script_name}"
        )

        sys.exit(result.returncode)

    print(
        f"\nPASS: {script_name}"
    )


# ==================================================
# PIPELINE COMPLETE
# ==================================================

print("\n" + "=" * 100)
print("PIPELINE COMPLETE")
print("=" * 100)

print("\nAll stages completed successfully.")