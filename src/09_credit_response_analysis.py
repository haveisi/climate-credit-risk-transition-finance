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

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

print("=" * 100)
print("CREDIT RESPONSE ANALYSIS")
print("=" * 100)

print("\nProject root:")
print(PROJECT_ROOT)

print("\nProcessed folder:")
print(PROCESSED_FOLDER)

print("\nOutput folder:")
print(OUTPUT_FOLDER)


# ==================================================
# 2. Load borrower sensitivity results
# ==================================================

SENSITIVITY_FILE = (
    OUTPUT_FOLDER
    / "borrower_sensitivity.csv"
)

if not SENSITIVITY_FILE.exists():
    raise FileNotFoundError(
        f"Sensitivity file not found:\n{SENSITIVITY_FILE}"
    )

df = pd.read_csv(
    SENSITIVITY_FILE
)

print("\nRows loaded:", len(df))


# ==================================================
# 3. Load borrower baseline credit data
# ==================================================

BORROWER_FILE = (
    PROCESSED_FOLDER
    / "borrower_inputs.csv"
)

if not BORROWER_FILE.exists():
    raise FileNotFoundError(
        f"Borrower file not found:\n{BORROWER_FILE}"
    )

borrowers = pd.read_csv(
    BORROWER_FILE
)

borrower_credit = borrowers[
    [
        "borrower",
        "baseline_pd",
        "baseline_lgd"
    ]
].copy()


# ==================================================
# 4. Merge credit inputs
# ==================================================

df = df.merge(
    borrower_credit,
    on="borrower",
    how="left"
)

required_columns = [
    "borrower",
    "ead",
    "baseline_pd",
    "baseline_lgd",
    "dscr",
    "net_leverage",
    "ebitda_change"
]

missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise KeyError(
        "Required columns missing: "
        + ", ".join(missing_columns)
    )

print("\nMerge check passed.")


# ==================================================
# 5. Load model caps
# ==================================================

ASSUMPTION_FILE = (
    PROCESSED_FOLDER
    / "model_assumptions.csv"
)

assumption_df = pd.read_csv(
    ASSUMPTION_FILE
)

assumptions = dict(
    zip(
        assumption_df["assumption"],
        assumption_df["value"]
    )
)

pd_cap = assumptions["PD cap"]
lgd_cap = assumptions["LGD cap"]


# ==================================================
# 6. Graduated PD multiplier
# ==================================================

def calculate_pd_multiplier(row):

    dscr = row["dscr"]
    leverage = row["net_leverage"]
    ebitda_change = row["ebitda_change"]

    multiplier = 1.0

    # DSCR stress
    if dscr < 0:
        multiplier = 6.0
    elif dscr < 0.50:
        multiplier = 5.0
    elif dscr < 0.75:
        multiplier = 4.0
    elif dscr < 1.00:
        multiplier = 3.0
    elif dscr < 1.20:
        multiplier = 2.0
    elif dscr < 1.50:
        multiplier = 1.5

    # Leverage overlay
    if leverage >= 4.0:
        multiplier += 2.0
    elif leverage >= 3.0:
        multiplier += 1.0
    elif leverage >= 2.5:
        multiplier += 0.5

    # EBITDA decline overlay
    if ebitda_change <= -0.50:
        multiplier += 2.0
    elif ebitda_change <= -0.35:
        multiplier += 1.0
    elif ebitda_change <= -0.20:
        multiplier += 0.5

    return multiplier


df["refined_pd_multiplier"] = df.apply(
    calculate_pd_multiplier,
    axis=1
)


# ==================================================
# 7. Refined stressed PD
# ==================================================

df["refined_stressed_pd"] = (
    df["baseline_pd"]
    * df["refined_pd_multiplier"]
)

df["refined_stressed_pd"] = (
    df["refined_stressed_pd"]
    .clip(upper=pd_cap)
)


# ==================================================
# 8. Refined LGD
# ==================================================

def calculate_refined_lgd(row):

    lgd = row["baseline_lgd"]
    ebitda_change = row["ebitda_change"]
    dscr = row["dscr"]

    if ebitda_change <= -0.50:
        lgd += 0.15
    elif ebitda_change <= -0.35:
        lgd += 0.10
    elif ebitda_change <= -0.20:
        lgd += 0.05

    if dscr < 0:
        lgd += 0.05

    return min(
        lgd,
        lgd_cap
    )


df["refined_stressed_lgd"] = df.apply(
    calculate_refined_lgd,
    axis=1
)


# ==================================================
# 9. Refined ECL
# ==================================================

df["refined_expected_credit_loss"] = (
    df["refined_stressed_pd"]
    * df["refined_stressed_lgd"]
    * df["ead"]
)

df["refined_ecl_rate"] = (
    df["refined_expected_credit_loss"]
    / df["ead"]
)


# ==================================================
# 10. Compare original vs refined
# ==================================================

df["ecl_change"] = (
    df["refined_expected_credit_loss"]
    - df["expected_credit_loss"]
)

df["ecl_change_pct"] = (
    df["ecl_change"]
    / df["expected_credit_loss"]
)


# ==================================================
# 11. Portfolio aggregation
# ==================================================

portfolio = (
    df.groupby(
        [
            "carbon_price",
            "price_impact",
            "volume_impact"
        ]
    )
    .agg(
        total_ead=(
            "ead",
            "sum"
        ),
        original_ecl=(
            "expected_credit_loss",
            "sum"
        ),
        refined_ecl=(
            "refined_expected_credit_loss",
            "sum"
        ),
        avg_dscr=(
            "dscr",
            "mean"
        ),
        avg_net_leverage=(
            "net_leverage",
            "mean"
        )
    )
    .reset_index()
)

portfolio["original_ecl_rate"] = (
    portfolio["original_ecl"]
    / portfolio["total_ead"]
)

portfolio["refined_ecl_rate"] = (
    portfolio["refined_ecl"]
    / portfolio["total_ead"]
)

portfolio["ecl_increase"] = (
    portfolio["refined_ecl"]
    - portfolio["original_ecl"]
)


# ==================================================
# 12. Worst cases
# ==================================================

worst_borrowers = (
    df.sort_values(
        "refined_expected_credit_loss",
        ascending=False
    )
    .head(20)
)

worst_portfolio = (
    portfolio.sort_values(
        "refined_ecl",
        ascending=False
    )
    .head(20)
)


# ==================================================
# 13. Print borrower results
# ==================================================

print("\nWORST BORROWER CASES")
print("=" * 100)

print(
    worst_borrowers[
        [
            "borrower",
            "carbon_price",
            "price_impact",
            "volume_impact",
            "dscr",
            "net_leverage",
            "ebitda_change",
            "refined_pd_multiplier",
            "refined_stressed_pd",
            "refined_stressed_lgd",
            "refined_expected_credit_loss",
            "refined_ecl_rate"
        ]
    ]
    .round(4)
    .to_string(index=False)
)


# ==================================================
# 14. Print portfolio results
# ==================================================

print("\nWORST PORTFOLIO CASES")
print("=" * 100)

print(
    worst_portfolio[
        [
            "carbon_price",
            "price_impact",
            "volume_impact",
            "avg_dscr",
            "avg_net_leverage",
            "original_ecl",
            "refined_ecl",
            "original_ecl_rate",
            "refined_ecl_rate",
            "ecl_increase"
        ]
    ]
    .round(4)
    .to_string(index=False)
)


# ==================================================
# 15. Export results
# ==================================================

borrower_output = (
    OUTPUT_FOLDER
    / "borrower_credit_response.csv"
)

portfolio_output = (
    OUTPUT_FOLDER
    / "portfolio_credit_response.csv"
)

worst_borrower_output = (
    OUTPUT_FOLDER
    / "worst_refined_borrower_cases.csv"
)

worst_portfolio_output = (
    OUTPUT_FOLDER
    / "worst_refined_portfolio_cases.csv"
)

df.to_csv(
    borrower_output,
    index=False
)

portfolio.to_csv(
    portfolio_output,
    index=False
)

worst_borrowers.to_csv(
    worst_borrower_output,
    index=False
)

worst_portfolio.to_csv(
    worst_portfolio_output,
    index=False
)


# ==================================================
# 16. Finish
# ==================================================

print("\n" + "=" * 100)
print("FILES CREATED")
print("=" * 100)

print(borrower_output)
print(portfolio_output)
print(worst_borrower_output)
print(worst_portfolio_output)

print(
    "\n09_credit_response_analysis.py "
    "finished successfully."
)