from pathlib import Path
import pandas as pd
import numpy as np


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

FILE_PATH = Path(
    r"C:\Users\hveis\OneDrive - UWSP\ESG\Finace emission\jpm_climate_credit_project\jpm_practice\ data\raw\jpm_practice.xlsx"
)

PROCESSED_FOLDER = FILE_PATH.parent.parent / "processed"

PYTHON_STRESS_FILE = (
    PROCESSED_FOLDER / "python_stress_results.csv"
)

PYTHON_PORTFOLIO_FILE = (
    PROCESSED_FOLDER / "python_portfolio_summary.csv"
)


# --------------------------------------------------
# 2. Check required files
# --------------------------------------------------

required_files = [
    FILE_PATH,
    PYTHON_STRESS_FILE,
    PYTHON_PORTFOLIO_FILE
]

for file in required_files:
    if not file.exists():
        raise FileNotFoundError(
            f"Required file not found:\n{file}"
        )

print("All required files found.")


# --------------------------------------------------
# 3. Load Python borrower stress results
# --------------------------------------------------

python_stress = pd.read_csv(
    PYTHON_STRESS_FILE
)

print(
    "\nPython stress rows:",
    len(python_stress)
)


# --------------------------------------------------
# 4. Load Excel borrower stress results
# --------------------------------------------------

excel_stress = pd.read_excel(
    FILE_PATH,
    sheet_name="O&G Borrower Stress Test",
    header=5,
    nrows=9,
    usecols="A:V"
)


# --------------------------------------------------
# 5. Rename Excel columns to match Python
# --------------------------------------------------

excel_stress = excel_stress.rename(
    columns={
        "Borrower": "borrower",
        "Scenario": "scenario",
        "Revenue ($mm)": "revenue",
        "EBITDA ($mm)": "ebitda",
        "EBITDA margin": "ebitda_margin",
        "Carbon cost ($mm)": "carbon_cost",
        "Transition capex ($mm)": "transition_capex",
        "CFADS ($mm)": "cfads",
        "Debt service ($mm)": "debt_service",
        "DSCR": "dscr",
        "Interest coverage": "interest_coverage",
        "Net leverage": "net_leverage",
        "EBITDA change": "ebitda_change",
        "Credit stress multiplier": "credit_stress_multiplier",
        "Stressed PD": "stressed_pd",
        "Stressed LGD": "stressed_lgd",
        "EAD ($mm)": "ead",
        "Expected credit loss ($mm)": "expected_credit_loss",
        "ECL / EAD": "ecl_rate",
        "Credit flag": "credit_flag"
    }
)


# --------------------------------------------------
# 6. Keep comparable columns
# --------------------------------------------------

numeric_columns = [
    "revenue",
    "ebitda",
    "ebitda_margin",
    "carbon_cost",
    "transition_capex",
    "cfads",
    "debt_service",
    "dscr",
    "interest_coverage",
    "net_leverage",
    "ebitda_change",
    "credit_stress_multiplier",
    "stressed_pd",
    "stressed_lgd",
    "ead",
    "expected_credit_loss",
    "ecl_rate"
]


# --------------------------------------------------
# 7. Merge Excel and Python results
# --------------------------------------------------

stress_compare = pd.merge(
    excel_stress[
        ["borrower", "scenario"] + numeric_columns
    ],
    python_stress[
        ["borrower", "scenario"] + numeric_columns
    ],
    on=[
        "borrower",
        "scenario"
    ],
    how="outer",
    suffixes=(
        "_excel",
        "_python"
    ),
    indicator=True
)


# --------------------------------------------------
# 8. Check missing rows
# --------------------------------------------------

print("\nROW MATCH CHECK")
print("=" * 100)

print(
    stress_compare["_merge"]
    .value_counts()
)


# --------------------------------------------------
# 9. Define tolerance
# --------------------------------------------------

ABSOLUTE_TOLERANCE = 0.01


# --------------------------------------------------
# 10. Compare each numeric metric
# --------------------------------------------------

qa_records = []

for _, row in stress_compare.iterrows():

    borrower = row["borrower"]
    scenario = row["scenario"]

    for metric in numeric_columns:

        excel_value = row.get(
            f"{metric}_excel"
        )

        python_value = row.get(
            f"{metric}_python"
        )

        # Handle missing values
        if pd.isna(excel_value) and pd.isna(python_value):
            difference = 0
            status = "PASS"

        elif pd.isna(excel_value) or pd.isna(python_value):
            difference = np.nan
            status = "FAIL - MISSING"

        else:

            difference = (
                python_value
                - excel_value
            )

            if np.isclose(
                python_value,
                excel_value,
                atol=ABSOLUTE_TOLERANCE,
                rtol=0
            ):
                status = "PASS"

            else:
                status = "FAIL"

        qa_records.append(
            {
                "borrower": borrower,
                "scenario": scenario,
                "metric": metric,
                "excel_value": excel_value,
                "python_value": python_value,
                "difference": difference,
                "status": status
            }
        )


# --------------------------------------------------
# 11. Create QA DataFrame
# --------------------------------------------------

qa_stress = pd.DataFrame(
    qa_records
)


# --------------------------------------------------
# 12. QA summary
# --------------------------------------------------

print("\nBORROWER MODEL QA SUMMARY")
print("=" * 100)

qa_summary = (
    qa_stress["status"]
    .value_counts()
)

print(qa_summary)


# --------------------------------------------------
# 13. Show failures only
# --------------------------------------------------

stress_failures = qa_stress[
    qa_stress["status"] != "PASS"
]

print("\nBORROWER MODEL FAILURES")
print("=" * 100)

if stress_failures.empty:

    print(
        "No borrower-level reconciliation failures."
    )

else:

    print(
        stress_failures.to_string(
            index=False
        )
    )


# ==================================================
# PORTFOLIO RECONCILIATION
# ==================================================


# --------------------------------------------------
# 14. Load Excel portfolio results
# --------------------------------------------------

excel_portfolio = pd.read_excel(
    FILE_PATH,
    sheet_name="O&G Portfolio Translation",
    header=6,
    nrows=3,
    usecols="A:K"
)


# --------------------------------------------------
# 15. Rename portfolio columns
# --------------------------------------------------

excel_portfolio = excel_portfolio.rename(
    columns={
        "Scenario": "scenario",
        "Practice sub-portfolio EAD ($mm)": "practice_ead",
        "Practice ECL ($mm)": "practice_ecl",
        "ECL rate": "ecl_rate",
        "JPM disclosed O&G exposure ($mm)": "jpm_disclosed_og_exposure",
        "Naive scaled loss ($mm)": "naive_scaled_loss",
        "Use scaled loss?": "use_scaled_loss",
        "Avg DSCR": "avg_dscr",
        "Avg interest coverage": "avg_interest_coverage",
        "Management interpretation": "management_interpretation"
    }
)


# --------------------------------------------------
# 16. Load Python portfolio results
# --------------------------------------------------

python_portfolio = pd.read_csv(
    PYTHON_PORTFOLIO_FILE
)


# --------------------------------------------------
# 17. Metrics to compare
# --------------------------------------------------

portfolio_metrics = [
    "practice_ead",
    "practice_ecl",
    "ecl_rate",
    "jpm_disclosed_og_exposure",
    "naive_scaled_loss",
    "avg_dscr",
    "avg_interest_coverage"
]


# --------------------------------------------------
# 18. Merge portfolio results
# --------------------------------------------------

portfolio_compare = pd.merge(
    excel_portfolio[
        ["scenario"] + portfolio_metrics
    ],
    python_portfolio[
        ["scenario"] + portfolio_metrics
    ],
    on="scenario",
    how="outer",
    suffixes=(
        "_excel",
        "_python"
    ),
    indicator=True
)


# --------------------------------------------------
# 19. Compare portfolio metrics
# --------------------------------------------------

portfolio_qa_records = []

for _, row in portfolio_compare.iterrows():

    scenario = row["scenario"]

    for metric in portfolio_metrics:

        excel_value = row.get(
            f"{metric}_excel"
        )

        python_value = row.get(
            f"{metric}_python"
        )

        if pd.isna(excel_value) and pd.isna(python_value):

            difference = 0
            status = "PASS"

        elif pd.isna(excel_value) or pd.isna(python_value):

            difference = np.nan
            status = "FAIL - MISSING"

        else:

            difference = (
                python_value
                - excel_value
            )

            if np.isclose(
                python_value,
                excel_value,
                atol=ABSOLUTE_TOLERANCE,
                rtol=0
            ):
                status = "PASS"

            else:
                status = "FAIL"

        portfolio_qa_records.append(
            {
                "scenario": scenario,
                "metric": metric,
                "excel_value": excel_value,
                "python_value": python_value,
                "difference": difference,
                "status": status
            }
        )


portfolio_qa = pd.DataFrame(
    portfolio_qa_records
)


# --------------------------------------------------
# 20. Portfolio QA summary
# --------------------------------------------------

print("\nPORTFOLIO QA SUMMARY")
print("=" * 100)

print(
    portfolio_qa["status"]
    .value_counts()
)


# --------------------------------------------------
# 21. Portfolio failures
# --------------------------------------------------

portfolio_failures = portfolio_qa[
    portfolio_qa["status"] != "PASS"
]

print("\nPORTFOLIO FAILURES")
print("=" * 100)

if portfolio_failures.empty:

    print(
        "No portfolio reconciliation failures."
    )

else:

    print(
        portfolio_failures.to_string(
            index=False
        )
    )


# --------------------------------------------------
# 22. Overall QA status
# --------------------------------------------------

total_failures = (
    len(stress_failures)
    + len(portfolio_failures)
)

print("\n" + "=" * 100)
print("OVERALL MODEL QA")
print("=" * 100)

if total_failures == 0:

    print(
        "PASS — Python model reconciles "
        "to Excel within tolerance."
    )

else:

    print(
        f"FAIL — {total_failures} "
        f"reconciliation exceptions found."
    )


# --------------------------------------------------
# 23. Export QA results
# --------------------------------------------------

qa_stress.to_csv(
    PROCESSED_FOLDER
    / "qa_borrower_reconciliation.csv",
    index=False
)

portfolio_qa.to_csv(
    PROCESSED_FOLDER
    / "qa_portfolio_reconciliation.csv",
    index=False
)

print("\nQA files exported:")
print(
    PROCESSED_FOLDER
    / "qa_borrower_reconciliation.csv"
)

print(
    PROCESSED_FOLDER
    / "qa_portfolio_reconciliation.csv"
)