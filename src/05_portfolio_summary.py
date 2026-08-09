from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. Locate files
# --------------------------------------------------

BASE_FOLDER = Path(
    r"C:\Users\hveis\OneDrive - UWSP\ESG\Finace emission\jpm_climate_credit_project\jpm_practice\ data"
)

PROCESSED_FOLDER = BASE_FOLDER / "processed"

stress_file = PROCESSED_FOLDER / "python_stress_results.csv"


# --------------------------------------------------
# 2. Load borrower-level stress results
# --------------------------------------------------

df = pd.read_csv(stress_file)

print("\nBorrower stress rows loaded:", len(df))


# --------------------------------------------------
# 3. Aggregate by scenario
# --------------------------------------------------

portfolio_summary = (
    df.groupby("scenario")
    .agg(
        practice_ead=("ead", "sum"),
        practice_ecl=("expected_credit_loss", "sum"),
        avg_dscr=("dscr", "mean"),
        avg_interest_coverage=("interest_coverage", "mean")
    )
    .reset_index()
)


# --------------------------------------------------
# 4. Calculate portfolio ECL rate
# --------------------------------------------------

portfolio_summary["ecl_rate"] = (
    portfolio_summary["practice_ecl"]
    / portfolio_summary["practice_ead"]
)


# --------------------------------------------------
# 5. Add JPM disclosed O&G exposure
# --------------------------------------------------

JPM_OG_EXPOSURE = 31724

portfolio_summary["jpm_disclosed_og_exposure"] = JPM_OG_EXPOSURE


# --------------------------------------------------
# 6. Calculate naive scaled loss
# --------------------------------------------------

portfolio_summary["naive_scaled_loss"] = (
    portfolio_summary["ecl_rate"]
    * portfolio_summary["jpm_disclosed_og_exposure"]
)


# --------------------------------------------------
# 7. Add scaling warning
# --------------------------------------------------

portfolio_summary["use_scaled_loss"] = "No"

portfolio_summary["scaling_reason"] = (
    "Synthetic borrowers are not proven representative of "
    "JPMorganChase's Oil & Gas portfolio. "
    "Use only as a sensitivity illustration."
)


# --------------------------------------------------
# 8. Management interpretation
# --------------------------------------------------

def management_interpretation(row):

    if row["scenario"] == "Current Policies-style":
        return "Reference credit profile"

    if row["avg_dscr"] < 1:
        return "Material deterioration — deeper review"

    return "Monitor"


portfolio_summary["management_interpretation"] = (
    portfolio_summary.apply(
        management_interpretation,
        axis=1
    )
)


# --------------------------------------------------
# 9. Reorder columns
# --------------------------------------------------

portfolio_summary = portfolio_summary[
    [
        "scenario",
        "practice_ead",
        "practice_ecl",
        "ecl_rate",
        "jpm_disclosed_og_exposure",
        "naive_scaled_loss",
        "use_scaled_loss",
        "scaling_reason",
        "avg_dscr",
        "avg_interest_coverage",
        "management_interpretation"
    ]
]


# --------------------------------------------------
# 10. Print results
# --------------------------------------------------

print("\nPORTFOLIO SUMMARY")
print("=" * 120)

print(
    portfolio_summary.round(
        {
            "practice_ead": 1,
            "practice_ecl": 3,
            "ecl_rate": 4,
            "jpm_disclosed_og_exposure": 1,
            "naive_scaled_loss": 1,
            "avg_dscr": 2,
            "avg_interest_coverage": 2
        }
    ).to_string(index=False)
)


# --------------------------------------------------
# 11. Export
# --------------------------------------------------

output_file = (
    PROCESSED_FOLDER
    / "python_portfolio_summary.csv"
)

portfolio_summary.to_csv(
    output_file,
    index=False
)

print("\nPortfolio summary exported to:")
print(output_file)