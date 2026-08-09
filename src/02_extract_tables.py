from pathlib import Path
import pandas as pd


# ==================================================
# 1. Locate project folders
# ==================================================

# This file lives inside /src, so parents[1] is jpm_practice
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Your current project appears to have a leading space
# in the data folder name, so support both versions.
DATA_FOLDER = PROJECT_ROOT / "data"

if not DATA_FOLDER.exists():
    DATA_FOLDER = PROJECT_ROOT / " data"

PROCESSED_FOLDER = DATA_FOLDER / "processed"
OUTPUT_FOLDER = PROJECT_ROOT / "outputs"

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

print("=" * 100)
print("EXPORT RESULTS")
print("=" * 100)

print("\nProject root:")
print(PROJECT_ROOT)

print("\nProcessed folder:")
print(PROCESSED_FOLDER)

print("\nProcessed folder exists:")
print(PROCESSED_FOLDER.exists())

print("\nOutput folder:")
print(OUTPUT_FOLDER)


# ==================================================
# 2. Define source files
# ==================================================

files = {
    "Scenario Inputs":
        PROCESSED_FOLDER / "scenario_inputs.csv",

    "Borrower Inputs":
        PROCESSED_FOLDER / "borrower_inputs.csv",

    "Model Assumptions":
        PROCESSED_FOLDER / "model_assumptions.csv",

    "Borrower Stress":
        PROCESSED_FOLDER / "python_stress_results.csv",

    "Portfolio Summary":
        PROCESSED_FOLDER / "python_portfolio_summary.csv",

    "Input Validation":
        PROCESSED_FOLDER / "input_validation_report.csv",

    "Borrower QA":
        PROCESSED_FOLDER / "qa_borrower_reconciliation.csv",

    "Portfolio QA":
        PROCESSED_FOLDER / "qa_portfolio_reconciliation.csv",

    "Workbook Inventory":
        PROCESSED_FOLDER / "workbook_inventory.csv",
}


# ==================================================
# 3. Check which files are available
# ==================================================

available_files = {}

print("\nFILES AVAILABLE FOR EXPORT")
print("=" * 100)

for name, path in files.items():

    if path.exists():

        available_files[name] = path
        print(f"FOUND:   {name}")

    else:

        print(f"MISSING: {name}")
        print(f"         {path}")


# ==================================================
# 4. Require critical outputs
# ==================================================

required_outputs = [
    "Borrower Stress",
    "Portfolio Summary",
    "Borrower QA",
    "Portfolio QA",
]

missing_required = [
    name
    for name in required_outputs
    if name not in available_files
]

if missing_required:

    raise FileNotFoundError(
        "Required output files are missing: "
        + ", ".join(missing_required)
    )


# ==================================================
# 5. Create consolidated Excel workbook
# ==================================================

excel_output = (
    OUTPUT_FOLDER
    / "JPM_Climate_Credit_Analytics_Output.xlsx"
)

print("\nCreating consolidated Excel workbook...")

with pd.ExcelWriter(
    excel_output,
    engine="openpyxl"
) as writer:

    for sheet_name, path in available_files.items():

        df = pd.read_csv(path)

        # Excel sheet names cannot exceed 31 characters
        safe_sheet_name = sheet_name[:31]

        df.to_excel(
            writer,
            sheet_name=safe_sheet_name,
            index=False
        )

print("Created:")
print(excel_output)


# ==================================================
# 6. Create Power BI borrower dataset
# ==================================================

borrower_stress = pd.read_csv(
    available_files["Borrower Stress"]
)

powerbi_borrower_file = (
    OUTPUT_FOLDER
    / "powerbi_borrower_stress.csv"
)

borrower_stress.to_csv(
    powerbi_borrower_file,
    index=False
)

print("\nCreated:")
print(powerbi_borrower_file)


# ==================================================
# 7. Create Power BI portfolio dataset
# ==================================================

portfolio_summary = pd.read_csv(
    available_files["Portfolio Summary"]
)

powerbi_portfolio_file = (
    OUTPUT_FOLDER
    / "powerbi_portfolio_summary.csv"
)

portfolio_summary.to_csv(
    powerbi_portfolio_file,
    index=False
)

print("\nCreated:")
print(powerbi_portfolio_file)


# ==================================================
# 8. Create executive scenario summary
# ==================================================

executive_columns = [
    "scenario",
    "practice_ead",
    "practice_ecl",
    "ecl_rate",
    "avg_dscr",
    "avg_interest_coverage",
    "management_interpretation",
]

missing_columns = [
    col
    for col in executive_columns
    if col not in portfolio_summary.columns
]

if missing_columns:

    raise KeyError(
        "Missing required portfolio columns: "
        + ", ".join(missing_columns)
    )

executive_summary = portfolio_summary[
    executive_columns
].copy()

executive_output = (
    OUTPUT_FOLDER
    / "executive_scenario_summary.csv"
)

executive_summary.to_csv(
    executive_output,
    index=False
)

print("\nCreated:")
print(executive_output)


# ==================================================
# 9. Create QA status summary
# ==================================================

borrower_qa = pd.read_csv(
    available_files["Borrower QA"]
)

portfolio_qa = pd.read_csv(
    available_files["Portfolio QA"]
)

borrower_failures = (
    borrower_qa["status"]
    .ne("PASS")
    .sum()
)

portfolio_failures = (
    portfolio_qa["status"]
    .ne("PASS")
    .sum()
)

qa_summary = pd.DataFrame(
    [
        {
            "control_area": "Borrower reconciliation",
            "failures": borrower_failures,
            "status": (
                "PASS"
                if borrower_failures == 0
                else "FAIL"
            )
        },
        {
            "control_area": "Portfolio reconciliation",
            "failures": portfolio_failures,
            "status": (
                "PASS"
                if portfolio_failures == 0
                else "FAIL"
            )
        }
    ]
)

qa_summary_file = (
    OUTPUT_FOLDER
    / "qa_status_summary.csv"
)

qa_summary.to_csv(
    qa_summary_file,
    index=False
)

print("\nCreated:")
print(qa_summary_file)


# ==================================================
# 10. Final export summary
# ==================================================

print("\n" + "=" * 100)
print("EXPORT COMPLETE")
print("=" * 100)

print("\nFinal outputs:")

print(
    "1. Consolidated Excel:",
    excel_output
)

print(
    "2. Power BI borrower dataset:",
    powerbi_borrower_file
)

print(
    "3. Power BI portfolio dataset:",
    powerbi_portfolio_file
)

print(
    "4. Executive scenario summary:",
    executive_output
)

print(
    "5. QA status summary:",
    qa_summary_file
)

print("\n07_export_results.py finished successfully.")