from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

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

available_files = {}

print("\nFILES AVAILABLE FOR EXPORT")
print("=" * 100)

for name, path in files.items():

    if path.exists():
        available_files[name] = path
        print(f"FOUND: {name}")

    else:
        print(f"MISSING: {name}")
        print(path)

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
        "Missing required outputs: "
        + ", ".join(missing_required)
    )

# --------------------------------------------------
# Consolidated Excel output
# --------------------------------------------------

excel_output = (
    OUTPUT_FOLDER
    / "JPM_Climate_Credit_Analytics_Output.xlsx"
)

with pd.ExcelWriter(
    excel_output,
    engine="openpyxl"
) as writer:

    for sheet_name, path in available_files.items():

        df = pd.read_csv(path)

        df.to_excel(
            writer,
            sheet_name=sheet_name[:31],
            index=False
        )

# --------------------------------------------------
# Power BI borrower output
# --------------------------------------------------

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

# --------------------------------------------------
# Power BI portfolio output
# --------------------------------------------------

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

# --------------------------------------------------
# Executive summary
# --------------------------------------------------

executive_columns = [
    "scenario",
    "practice_ead",
    "practice_ecl",
    "ecl_rate",
    "avg_dscr",
    "avg_interest_coverage",
    "management_interpretation",
]

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

# --------------------------------------------------
# QA summary
# --------------------------------------------------

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

print("\n" + "=" * 100)
print("EXPORT COMPLETE")
print("=" * 100)

print("\nCreated:")
print(excel_output)
print(powerbi_borrower_file)
print(powerbi_portfolio_file)
print(executive_output)
print(qa_summary_file)

print("\n07_export_results.py finished successfully.")