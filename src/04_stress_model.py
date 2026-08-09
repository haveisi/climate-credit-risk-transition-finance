from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. Locate processed data folder
# --------------------------------------------------

BASE_FOLDER = Path(
    r"C:\Users\hveis\OneDrive - UWSP\ESG\Finace emission\jpm_climate_credit_project\jpm_practice\ data"
)

PROCESSED_FOLDER = BASE_FOLDER / "processed"

scenario_file = PROCESSED_FOLDER / "scenario_inputs.csv"
borrower_file = PROCESSED_FOLDER / "borrower_inputs.csv"
assumption_file = PROCESSED_FOLDER / "model_assumptions.csv"


# --------------------------------------------------
# 2. Load clean processed inputs
# --------------------------------------------------

scenario_inputs = pd.read_csv(scenario_file)
borrower_inputs = pd.read_csv(borrower_file)
model_assumptions = pd.read_csv(assumption_file)

assumptions = dict(
    zip(
        model_assumptions["assumption"],
        model_assumptions["value"]
    )
)

cash_tax_rate = assumptions["Cash tax rate on EBITDA"]
pd_cap = assumptions["PD cap"]
lgd_cap = assumptions["LGD cap"]


# --------------------------------------------------
# 3. Create borrower x scenario combinations
# --------------------------------------------------

results = []

for _, borrower in borrower_inputs.iterrows():

    for _, scenario in scenario_inputs.iterrows():

        borrower_name = borrower["borrower"]
        scenario_name = scenario["scenario"]

        baseline_revenue = borrower["revenue"]
        baseline_ebitda = borrower["ebitda"]

        price_impact = scenario["price_impact"]
        volume_impact = scenario["volume_impact"]

        additional_opex_pct = scenario["additional_opex_pct"]
        carbon_price = scenario["carbon_price"]
        transition_capex_pct = scenario["transition_capex_pct"]


        # --------------------------------------------------
        # 4. Revenue
        # --------------------------------------------------

        stressed_revenue = (
            baseline_revenue
            * (1 + price_impact)
            * (1 + volume_impact)
        )


        # --------------------------------------------------
        # 5. Baseline EBITDA margin
        # --------------------------------------------------

        baseline_ebitda_margin = (
            baseline_ebitda / baseline_revenue
        )


        # --------------------------------------------------
        # 6. Pre-carbon stressed EBITDA
        # --------------------------------------------------

        stressed_ebitda_before_carbon = (
            stressed_revenue
            * baseline_ebitda_margin
            - stressed_revenue * additional_opex_pct
        )


        # --------------------------------------------------
        # 7. Direct emissions estimate
        # --------------------------------------------------

        stressed_emissions = (
            borrower["emissions_intensity"]
            * stressed_revenue
        )


        # --------------------------------------------------
        # 8. Carbon cost
        # --------------------------------------------------

        carbon_cost = (
            stressed_emissions
            * carbon_price
            / 1_000_000
        )


        # --------------------------------------------------
        # 9. Final stressed EBITDA
        # --------------------------------------------------

        stressed_ebitda = (
            stressed_ebitda_before_carbon
            - carbon_cost
        )


        # --------------------------------------------------
        # 10. EBITDA margin
        # --------------------------------------------------

        ebitda_margin = (
            stressed_ebitda / stressed_revenue
        )


        # --------------------------------------------------
        # 11. Transition CAPEX
        # --------------------------------------------------

        transition_capex = (
            stressed_revenue
            * transition_capex_pct
        )


        # --------------------------------------------------
        # 12. Cash taxes
        # --------------------------------------------------

        cash_taxes = (
            stressed_ebitda
            * cash_tax_rate
        )


        # --------------------------------------------------
        # 13. CFADS
        # --------------------------------------------------

        cfads = (
            stressed_ebitda
            - cash_taxes
            - borrower["maintenance_capex"]
            - transition_capex
        )


        # --------------------------------------------------
        # 14. Debt service
        # --------------------------------------------------

        debt_service = (
            borrower["interest_expense"]
            + borrower["scheduled_principal"]
        )


        # --------------------------------------------------
        # 15. DSCR
        # --------------------------------------------------

        dscr = (
            cfads / debt_service
            if debt_service != 0
            else None
        )


        # --------------------------------------------------
        # 16. Interest coverage
        # --------------------------------------------------

        interest_coverage = (
            stressed_ebitda
            / borrower["interest_expense"]
            if borrower["interest_expense"] != 0
            else None
        )


        # --------------------------------------------------
        # 17. Net leverage
        # --------------------------------------------------

        net_debt = (
            borrower["debt"]
            - borrower["cash"]
        )

        net_leverage = (
            net_debt / stressed_ebitda
            if stressed_ebitda != 0
            else None
        )


        # --------------------------------------------------
        # 18. EBITDA change
        # --------------------------------------------------

        ebitda_change = (
            stressed_ebitda / baseline_ebitda
        ) - 1


        # --------------------------------------------------
        # 19. Credit stress multiplier
        # --------------------------------------------------

        if scenario_name == "Current Policies-style":
            credit_stress_multiplier = 1

        else:
            credit_stress_multiplier = 5


        # --------------------------------------------------
        # 20. Stressed PD
        # --------------------------------------------------

        stressed_pd = min(
            borrower["baseline_pd"]
            * credit_stress_multiplier,
            pd_cap
        )


        # --------------------------------------------------
        # 21. Stressed LGD
        # --------------------------------------------------

        stressed_lgd = borrower["baseline_lgd"]

        if scenario_name == "Accelerated Transition":

            if ebitda_change < -0.20:
                stressed_lgd += 0.05

        elif scenario_name == "Severe Transition":

            if ebitda_change < -0.35:
                stressed_lgd += 0.10

        stressed_lgd = min(
            stressed_lgd,
            lgd_cap
        )


        # --------------------------------------------------
        # 22. EAD
        # --------------------------------------------------

        ead = borrower["ead"]


        # --------------------------------------------------
        # 23. Expected Credit Loss
        # --------------------------------------------------

        expected_credit_loss = (
            stressed_pd
            * stressed_lgd
            * ead
        )


        # --------------------------------------------------
        # 24. ECL / EAD
        # --------------------------------------------------

        ecl_rate = (
            expected_credit_loss / ead
            if ead != 0
            else None
        )


        # --------------------------------------------------
        # 25. Credit flag
        # --------------------------------------------------

        if scenario_name == "Current Policies-style":
            credit_flag = "Reference"

        elif dscr is not None and dscr < 1:
            credit_flag = "Severe"

        else:
            credit_flag = "Monitor"


        # --------------------------------------------------
        # 26. Append results
        # --------------------------------------------------

        results.append(
            {
                "borrower": borrower_name,
                "scenario": scenario_name,
                "revenue": stressed_revenue,
                "ebitda": stressed_ebitda,
                "ebitda_margin": ebitda_margin,
                "carbon_cost": carbon_cost,
                "transition_capex": transition_capex,
                "cfads": cfads,
                "debt_service": debt_service,
                "dscr": dscr,
                "interest_coverage": interest_coverage,
                "net_leverage": net_leverage,
                "ebitda_change": ebitda_change,
                "credit_stress_multiplier": credit_stress_multiplier,
                "stressed_pd": stressed_pd,
                "stressed_lgd": stressed_lgd,
                "ead": ead,
                "expected_credit_loss": expected_credit_loss,
                "ecl_rate": ecl_rate,
                "credit_flag": credit_flag,
            }
        )


# --------------------------------------------------
# 27. Convert results to DataFrame
# --------------------------------------------------

stress_results = pd.DataFrame(results)


# --------------------------------------------------
# 28. Display results
# --------------------------------------------------

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)

print("\nBORROWER STRESS RESULTS")
print("=" * 120)

print(
    stress_results.round(
        {
            "revenue": 1,
            "ebitda": 1,
            "ebitda_margin": 4,
            "carbon_cost": 1,
            "transition_capex": 1,
            "cfads": 1,
            "debt_service": 1,
            "dscr": 2,
            "interest_coverage": 2,
            "net_leverage": 2,
            "ebitda_change": 4,
            "stressed_pd": 4,
            "stressed_lgd": 4,
            "expected_credit_loss": 2,
            "ecl_rate": 4
        }
    ).to_string(index=False)
)


# --------------------------------------------------
# 29. Export results
# --------------------------------------------------

OUTPUT_FOLDER = BASE_FOLDER / "processed"

output_file = OUTPUT_FOLDER / "python_stress_results.csv"

stress_results.to_csv(
    output_file,
    index=False
)

print("\nResults exported to:")
print(output_file)