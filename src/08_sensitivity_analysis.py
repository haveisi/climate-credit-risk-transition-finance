from pathlib import Path
import pandas as pd


# ==================================================
# 1. Locate project folders
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FOLDER = PROJECT_ROOT / "data"

# Support current folder that may contain a leading space
if not DATA_FOLDER.exists():
    DATA_FOLDER = PROJECT_ROOT / " data"

PROCESSED_FOLDER = DATA_FOLDER / "processed"
OUTPUT_FOLDER = PROJECT_ROOT / "outputs"

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

print("=" * 100)
print("CLIMATE CREDIT SENSITIVITY ANALYSIS")
print("=" * 100)

print("\nProject root:")
print(PROJECT_ROOT)

print("\nProcessed folder:")
print(PROCESSED_FOLDER)


# ==================================================
# 2. Input files
# ==================================================

borrower_file = (
    PROCESSED_FOLDER
    / "borrower_inputs.csv"
)

assumption_file = (
    PROCESSED_FOLDER
    / "model_assumptions.csv"
)

required_files = [
    borrower_file,
    assumption_file
]

for file in required_files:

    if not file.exists():
        raise FileNotFoundError(
            f"Required file missing:\n{file}"
        )


# ==================================================
# 3. Load inputs
# ==================================================

borrowers = pd.read_csv(
    borrower_file
)

model_assumptions = pd.read_csv(
    assumption_file
)

assumptions = dict(
    zip(
        model_assumptions["assumption"],
        model_assumptions["value"]
    )
)

cash_tax_rate = assumptions[
    "Cash tax rate on EBITDA"
]

pd_cap = assumptions[
    "PD cap"
]

lgd_cap = assumptions[
    "LGD cap"
]


# ==================================================
# 4. Define sensitivity grid
# ==================================================

carbon_prices = [
    0,
    50,
    75,
    100,
    150,
    200
]

price_shocks = [
    0.00,
    -0.05,
    -0.10,
    -0.15,
    -0.20,
    -0.25
]

demand_shocks = [
    0.00,
    -0.05,
    -0.10,
    -0.15
]


# Keep these fixed initially so we isolate
# the three main sensitivity drivers.
ADDITIONAL_OPEX_PCT = 0.01
TRANSITION_CAPEX_PCT = 0.05


# ==================================================
# 5. Stress function
# ==================================================

def calculate_stress(
    borrower,
    carbon_price,
    price_impact,
    volume_impact
):

    baseline_revenue = borrower["revenue"]
    baseline_ebitda = borrower["ebitda"]

    baseline_margin = (
        baseline_ebitda
        / baseline_revenue
    )

    # ----------------------------------------------
    # Revenue shock
    # ----------------------------------------------

    stressed_revenue = (
        baseline_revenue
        * (1 + price_impact)
        * (1 + volume_impact)
    )

    # ----------------------------------------------
    # Operating cost pressure
    # ----------------------------------------------

    additional_opex = (
        stressed_revenue
        * ADDITIONAL_OPEX_PCT
    )

    # ----------------------------------------------
    # Emissions estimate
    # ----------------------------------------------

    stressed_emissions = (
        borrower["emissions_intensity"]
        * stressed_revenue
    )

    # ----------------------------------------------
    # Carbon cost
    # ----------------------------------------------

    carbon_cost = (
        stressed_emissions
        * carbon_price
        / 1_000_000
    )

    # ----------------------------------------------
    # EBITDA
    # ----------------------------------------------

    stressed_ebitda = (
        stressed_revenue
        * baseline_margin
        - additional_opex
        - carbon_cost
    )

    # ----------------------------------------------
    # EBITDA change
    # ----------------------------------------------

    ebitda_change = (
        stressed_ebitda
        / baseline_ebitda
    ) - 1

    # ----------------------------------------------
    # Transition CAPEX
    # ----------------------------------------------

    transition_capex = (
        stressed_revenue
        * TRANSITION_CAPEX_PCT
    )

    # ----------------------------------------------
    # Cash taxes
    # ----------------------------------------------

    cash_taxes = (
        stressed_ebitda
        * cash_tax_rate
    )

    # ----------------------------------------------
    # CFADS
    # ----------------------------------------------

    cfads = (
        stressed_ebitda
        - cash_taxes
        - borrower["maintenance_capex"]
        - transition_capex
    )

    # ----------------------------------------------
    # Debt service
    # ----------------------------------------------

    debt_service = (
        borrower["interest_expense"]
        + borrower["scheduled_principal"]
    )

    # ----------------------------------------------
    # DSCR
    # ----------------------------------------------

    if debt_service != 0:
        dscr = cfads / debt_service
    else:
        dscr = None

    # ----------------------------------------------
    # Interest coverage
    # ----------------------------------------------

    if borrower["interest_expense"] != 0:
        interest_coverage = (
            stressed_ebitda
            / borrower["interest_expense"]
        )
    else:
        interest_coverage = None

    # ----------------------------------------------
    # Net leverage
    # ----------------------------------------------

    net_debt = (
        borrower["debt"]
        - borrower["cash"]
    )

    if stressed_ebitda != 0:
        net_leverage = (
            net_debt
            / stressed_ebitda
        )
    else:
        net_leverage = None

    # ----------------------------------------------
    # Simple PD stress logic
    # ----------------------------------------------

    if (
        price_impact == 0
        and volume_impact == 0
        and carbon_price == 0
    ):
        multiplier = 1

    elif (
        dscr is not None
        and dscr < 1
    ):
        multiplier = 5

    elif (
        net_leverage is not None
        and net_leverage > 3
    ):
        multiplier = 4

    else:
        multiplier = 2

    stressed_pd = min(
        borrower["baseline_pd"]
        * multiplier,
        pd_cap
    )

    # ----------------------------------------------
    # LGD stress logic
    # ----------------------------------------------

    stressed_lgd = borrower[
        "baseline_lgd"
    ]

    if ebitda_change < -0.35:
        stressed_lgd += 0.10

    elif ebitda_change < -0.20:
        stressed_lgd += 0.05

    stressed_lgd = min(
        stressed_lgd,
        lgd_cap
    )

    # ----------------------------------------------
    # Expected Credit Loss
    # ----------------------------------------------

    ead = borrower["ead"]

    expected_credit_loss = (
        stressed_pd
        * stressed_lgd
        * ead
    )

    ecl_rate = (
        expected_credit_loss / ead
        if ead != 0
        else None
    )

    return {
        "borrower":
            borrower["borrower"],

        "business_type":
            borrower["business_type"],

        "carbon_price":
            carbon_price,

        "price_impact":
            price_impact,

        "volume_impact":
            volume_impact,

        "revenue":
            stressed_revenue,

        "ebitda":
            stressed_ebitda,

        "ebitda_change":
            ebitda_change,

        "carbon_cost":
            carbon_cost,

        "transition_capex":
            transition_capex,

        "cfads":
            cfads,

        "dscr":
            dscr,

        "interest_coverage":
            interest_coverage,

        "net_leverage":
            net_leverage,

        "pd_multiplier":
            multiplier,

        "stressed_pd":
            stressed_pd,

        "stressed_lgd":
            stressed_lgd,

        "ead":
            ead,

        "expected_credit_loss":
            expected_credit_loss,

        "ecl_rate":
            ecl_rate
    }


# ==================================================
# 6. Run sensitivity combinations
# ==================================================

results = []

for _, borrower in borrowers.iterrows():

    for carbon_price in carbon_prices:

        for price_impact in price_shocks:

            for volume_impact in demand_shocks:

                result = calculate_stress(
                    borrower=borrower,
                    carbon_price=carbon_price,
                    price_impact=price_impact,
                    volume_impact=volume_impact
                )

                results.append(
                    result
                )


sensitivity_df = pd.DataFrame(
    results
)


# ==================================================
# 7. Portfolio aggregation
# ==================================================

portfolio_sensitivity = (
    sensitivity_df
    .groupby(
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
        total_ecl=(
            "expected_credit_loss",
            "sum"
        ),
        avg_dscr=(
            "dscr",
            "mean"
        ),
        avg_interest_coverage=(
            "interest_coverage",
            "mean"
        ),
        avg_net_leverage=(
            "net_leverage",
            "mean"
        )
    )
    .reset_index()
)


portfolio_sensitivity[
    "portfolio_ecl_rate"
] = (
    portfolio_sensitivity[
        "total_ecl"
    ]
    /
    portfolio_sensitivity[
        "total_ead"
    ]
)


# ==================================================
# 8. Identify worst cases
# ==================================================

worst_borrower_cases = (
    sensitivity_df
    .sort_values(
        "expected_credit_loss",
        ascending=False
    )
    .head(20)
)

worst_portfolio_cases = (
    portfolio_sensitivity
    .sort_values(
        "total_ecl",
        ascending=False
    )
    .head(20)
)


# ==================================================
# 9. Print useful summary
# ==================================================

print("\nSENSITIVITY RUN COMPLETE")
print("=" * 100)

print(
    "Borrower sensitivity rows:",
    len(sensitivity_df)
)

print(
    "Portfolio sensitivity rows:",
    len(portfolio_sensitivity)
)

print("\nWorst borrower cases:")
print(
    worst_borrower_cases[
        [
            "borrower",
            "carbon_price",
            "price_impact",
            "volume_impact",
            "dscr",
            "net_leverage",
            "expected_credit_loss",
            "ecl_rate"
        ]
    ]
    .round(4)
    .to_string(index=False)
)


print("\nWorst portfolio cases:")
print(
    worst_portfolio_cases[
        [
            "carbon_price",
            "price_impact",
            "volume_impact",
            "total_ecl",
            "portfolio_ecl_rate",
            "avg_dscr",
            "avg_net_leverage"
        ]
    ]
    .round(4)
    .to_string(index=False)
)


# ==================================================
# 10. Export results
# ==================================================

borrower_output = (
    OUTPUT_FOLDER
    / "borrower_sensitivity.csv"
)

portfolio_output = (
    OUTPUT_FOLDER
    / "portfolio_sensitivity.csv"
)

worst_borrower_output = (
    OUTPUT_FOLDER
    / "worst_borrower_cases.csv"
)

worst_portfolio_output = (
    OUTPUT_FOLDER
    / "worst_portfolio_cases.csv"
)


sensitivity_df.to_csv(
    borrower_output,
    index=False
)

portfolio_sensitivity.to_csv(
    portfolio_output,
    index=False
)

worst_borrower_cases.to_csv(
    worst_borrower_output,
    index=False
)

worst_portfolio_cases.to_csv(
    worst_portfolio_output,
    index=False
)


print("\n" + "=" * 100)
print("FILES CREATED")
print("=" * 100)

print(borrower_output)
print(portfolio_output)
print(worst_borrower_output)
print(worst_portfolio_output)

print(
    "\n08_sensitivity_analysis.py "
    "finished successfully."
)