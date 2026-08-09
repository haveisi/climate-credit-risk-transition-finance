from pathlib import Path
import pandas as pd


# ==================================================
# 1. Locate project folders
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FOLDER = PROJECT_ROOT / "data"

if not DATA_FOLDER.exists():
    DATA_FOLDER = PROJECT_ROOT / " data"

PROCESSED_FOLDER = DATA_FOLDER / "processed"
OUTPUT_FOLDER = PROJECT_ROOT / "outputs"
POWERBI_FOLDER = OUTPUT_FOLDER / "powerbi"

POWERBI_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

print("=" * 100)
print("POWER BI DATA PREPARATION")
print("=" * 100)

print("\nProject root:")
print(PROJECT_ROOT)

print("\nPower BI output folder:")
print(POWERBI_FOLDER)


# ==================================================
# 2. Define required source files
# ==================================================

BORROWER_RESPONSE_FILE = (
    OUTPUT_FOLDER
    / "borrower_credit_response.csv"
)

PORTFOLIO_RESPONSE_FILE = (
    OUTPUT_FOLDER
    / "portfolio_credit_response.csv"
)

WORST_BORROWER_FILE = (
    OUTPUT_FOLDER
    / "worst_refined_borrower_cases.csv"
)

WORST_PORTFOLIO_FILE = (
    OUTPUT_FOLDER
    / "worst_refined_portfolio_cases.csv"
)

QA_STATUS_FILE = (
    OUTPUT_FOLDER
    / "qa_status_summary.csv"
)

BORROWER_INPUT_FILE = (
    PROCESSED_FOLDER
    / "borrower_inputs.csv"
)

SCENARIO_INPUT_FILE = (
    PROCESSED_FOLDER
    / "scenario_inputs.csv"
)


required_files = [
    BORROWER_RESPONSE_FILE,
    PORTFOLIO_RESPONSE_FILE,
    BORROWER_INPUT_FILE,
    SCENARIO_INPUT_FILE
]


for file in required_files:

    if not file.exists():
        raise FileNotFoundError(
            f"Required file missing:\n{file}"
        )


# ==================================================
# 3. Load source datasets
# ==================================================

borrower_response = pd.read_csv(
    BORROWER_RESPONSE_FILE
)

portfolio_response = pd.read_csv(
    PORTFOLIO_RESPONSE_FILE
)

borrower_inputs = pd.read_csv(
    BORROWER_INPUT_FILE
)

scenario_inputs = pd.read_csv(
    SCENARIO_INPUT_FILE
)


print("\nRows loaded:")

print(
    "Borrower response:",
    len(borrower_response)
)

print(
    "Portfolio response:",
    len(portfolio_response)
)


# ==================================================
# 4. Borrower scenario fact table
# ==================================================

borrower_fact_columns = [
    "borrower",
    "business_type",
    "carbon_price",
    "price_impact",
    "volume_impact",
    "revenue",
    "ebitda",
    "ebitda_change",
    "carbon_cost",
    "transition_capex",
    "cfads",
    "dscr",
    "interest_coverage",
    "net_leverage",
    "baseline_pd",
    "baseline_lgd",
    "refined_pd_multiplier",
    "refined_stressed_pd",
    "refined_stressed_lgd",
    "ead",
    "expected_credit_loss",
    "refined_expected_credit_loss",
    "ecl_rate",
    "refined_ecl_rate",
    "ecl_change"
]

missing_columns = [
    col
    for col in borrower_fact_columns
    if col not in borrower_response.columns
]

if missing_columns:

    raise KeyError(
        "Missing borrower fact columns: "
        + ", ".join(missing_columns)
    )


borrower_fact = borrower_response[
    borrower_fact_columns
].copy()


# ==================================================
# 5. Add useful analyst flags
# ==================================================

borrower_fact[
    "dscr_below_1"
] = borrower_fact[
    "dscr"
] < 1


borrower_fact[
    "negative_cfads"
] = borrower_fact[
    "cfads"
] < 0


borrower_fact[
    "high_leverage"
] = borrower_fact[
    "net_leverage"
] >= 3


borrower_fact[
    "large_ebitda_decline"
] = borrower_fact[
    "ebitda_change"
] <= -0.35


# ==================================================
# 6. Create borrower risk category
# ==================================================

def borrower_risk_category(row):

    if row["cfads"] < 0:
        return "Critical"

    if (
        row["dscr"] < 0.50
        or row["refined_ecl_rate"] >= 0.075
    ):
        return "High"

    if (
        row["dscr"] < 1.00
        or row["net_leverage"] >= 3
    ):
        return "Elevated"

    if row["dscr"] < 1.20:
        return "Watch"

    return "Stable"


borrower_fact[
    "risk_category"
] = borrower_fact.apply(
    borrower_risk_category,
    axis=1
)


# ==================================================
# 7. Create scenario ID
# ==================================================

borrower_fact[
    "scenario_id"
] = (
    "CP_"
    + borrower_fact["carbon_price"].astype(str)
    + "_P_"
    + borrower_fact["price_impact"].astype(str)
    + "_V_"
    + borrower_fact["volume_impact"].astype(str)
)


# ==================================================
# 8. Portfolio scenario fact table
# ==================================================

portfolio_fact = portfolio_response.copy()


portfolio_fact[
    "scenario_id"
] = (
    "CP_"
    + portfolio_fact["carbon_price"].astype(str)
    + "_P_"
    + portfolio_fact["price_impact"].astype(str)
    + "_V_"
    + portfolio_fact["volume_impact"].astype(str)
)


portfolio_fact[
    "portfolio_dscr_below_1"
] = (
    portfolio_fact["avg_dscr"] < 1
)


portfolio_fact[
    "portfolio_high_leverage"
] = (
    portfolio_fact["avg_net_leverage"] >= 3
)


# ==================================================
# 9. Portfolio risk category
# ==================================================

def portfolio_risk_category(row):

    if row["avg_dscr"] < 0:
        return "Critical"

    if row["avg_dscr"] < 0.50:
        return "High"

    if row["avg_dscr"] < 1.00:
        return "Elevated"

    if row["avg_dscr"] < 1.20:
        return "Watch"

    return "Stable"


portfolio_fact[
    "portfolio_risk_category"
] = portfolio_fact.apply(
    portfolio_risk_category,
    axis=1
)


# ==================================================
# 10. Borrower dimension table
# ==================================================

borrower_dim = borrower_inputs[
    [
        "borrower",
        "business_type",
        "revenue",
        "ebitda",
        "debt",
        "cash",
        "interest_expense",
        "maintenance_capex",
        "scheduled_principal",
        "emissions_intensity",
        "ead",
        "baseline_pd",
        "baseline_lgd"
    ]
].copy()


borrower_dim = borrower_dim.rename(
    columns={
        "revenue":
            "baseline_revenue",

        "ebitda":
            "baseline_ebitda",

        "debt":
            "baseline_debt",

        "cash":
            "baseline_cash"
    }
)


# ==================================================
# 11. Scenario dimension table
# ==================================================

scenario_dim = (
    borrower_fact[
        [
            "scenario_id",
            "carbon_price",
            "price_impact",
            "volume_impact"
        ]
    ]
    .drop_duplicates()
    .reset_index(drop=True)
)


# ==================================================
# 12. Driver severity measures
# ==================================================

scenario_dim[
    "price_shock_pct"
] = (
    scenario_dim["price_impact"]
    * 100
)

scenario_dim[
    "volume_shock_pct"
] = (
    scenario_dim["volume_impact"]
    * 100
)


scenario_dim[
    "combined_market_shock"
] = (
    1
    -
    (
        (1 + scenario_dim["price_impact"])
        *
        (1 + scenario_dim["volume_impact"])
    )
)


scenario_dim[
    "combined_market_shock_pct"
] = (
    scenario_dim[
        "combined_market_shock"
    ]
    * 100
)


# ==================================================
# 13. Executive borrower ranking
# ==================================================

borrower_ranking = (
    borrower_fact
    .groupby(
        [
            "borrower",
            "business_type"
        ]
    )
    .agg(
        worst_dscr=(
            "dscr",
            "min"
        ),
        highest_leverage=(
            "net_leverage",
            "max"
        ),
        max_refined_ecl=(
            "refined_expected_credit_loss",
            "max"
        ),
        max_refined_ecl_rate=(
            "refined_ecl_rate",
            "max"
        ),
        worst_ebitda_change=(
            "ebitda_change",
            "min"
        ),
        critical_cases=(
            "negative_cfads",
            "sum"
        ),
        stressed_cases=(
            "dscr_below_1",
            "sum"
        )
    )
    .reset_index()
)


borrower_ranking[
    "risk_rank"
] = borrower_ranking[
    "max_refined_ecl_rate"
].rank(
    method="dense",
    ascending=False
).astype(int)


borrower_ranking = borrower_ranking.sort_values(
    "risk_rank"
)


# ==================================================
# 14. Executive portfolio summary
# ==================================================

portfolio_executive = (
    portfolio_fact
    .sort_values(
        "refined_ecl",
        ascending=False
    )
    .head(25)
    .copy()
)


# ==================================================
# 15. QA summary
# ==================================================

if QA_STATUS_FILE.exists():

    qa_status = pd.read_csv(
        QA_STATUS_FILE
    )

else:

    qa_status = pd.DataFrame(
        [
            {
                "control_area":
                    "QA status file",

                "failures":
                    None,

                "status":
                    "Not available"
            }
        ]
    )


# ==================================================
# 16. Optional worst-case tables
# ==================================================

if WORST_BORROWER_FILE.exists():

    worst_borrowers = pd.read_csv(
        WORST_BORROWER_FILE
    )

else:

    worst_borrowers = pd.DataFrame()


if WORST_PORTFOLIO_FILE.exists():

    worst_portfolio = pd.read_csv(
        WORST_PORTFOLIO_FILE
    )

else:

    worst_portfolio = pd.DataFrame()


# ==================================================
# 17. Export Power BI tables
# ==================================================

outputs = {
    "fact_borrower_sensitivity.csv":
        borrower_fact,

    "fact_portfolio_sensitivity.csv":
        portfolio_fact,

    "dim_borrower.csv":
        borrower_dim,

    "dim_scenario.csv":
        scenario_dim,

    "borrower_ranking.csv":
        borrower_ranking,

    "portfolio_executive.csv":
        portfolio_executive,

    "qa_status.csv":
        qa_status
}


for filename, dataframe in outputs.items():

    path = (
        POWERBI_FOLDER
        / filename
    )

    dataframe.to_csv(
        path,
        index=False
    )

    print(
        f"Created: {path}"
    )


# ==================================================
# 18. Export optional tables
# ==================================================

if not worst_borrowers.empty:

    worst_borrowers.to_csv(
        POWERBI_FOLDER
        / "worst_borrower_cases.csv",
        index=False
    )


if not worst_portfolio.empty:

    worst_portfolio.to_csv(
        POWERBI_FOLDER
        / "worst_portfolio_cases.csv",
        index=False
    )


# ==================================================
# 19. Print ranking
# ==================================================

print("\nBORROWER RISK RANKING")
print("=" * 100)

print(
    borrower_ranking[
        [
            "risk_rank",
            "borrower",
            "worst_dscr",
            "highest_leverage",
            "max_refined_ecl",
            "max_refined_ecl_rate",
            "critical_cases",
            "stressed_cases"
        ]
    ]
    .round(4)
    .to_string(
        index=False
    )
)


# ==================================================
# 20. Final controls
# ==================================================

print("\nDATA MODEL COUNTS")
print("=" * 100)

print(
    "Borrower fact rows:",
    len(borrower_fact)
)

print(
    "Portfolio fact rows:",
    len(portfolio_fact)
)

print(
    "Borrowers:",
    borrower_dim["borrower"].nunique()
)

print(
    "Scenarios:",
    scenario_dim["scenario_id"].nunique()
)


# ==================================================
# 21. Finish
# ==================================================

print("\n" + "=" * 100)
print("POWER BI PREPARATION COMPLETE")
print("=" * 100)

print(
    "\n10_powerbi_prep.py "
    "finished successfully."
)