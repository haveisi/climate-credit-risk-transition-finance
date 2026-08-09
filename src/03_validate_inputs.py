from pathlib import Path
import pandas as pd


# ==================================================
# 1. Locate folders
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FOLDER = PROJECT_ROOT / "data"

if not DATA_FOLDER.exists():
    DATA_FOLDER = PROJECT_ROOT / " data"

PROCESSED_FOLDER = DATA_FOLDER / "processed"


# ==================================================
# 2. Required input files
# ==================================================

scenario_file = (
    PROCESSED_FOLDER
    / "scenario_inputs.csv"
)

borrower_file = (
    PROCESSED_FOLDER
    / "borrower_inputs.csv"
)

assumption_file = (
    PROCESSED_FOLDER
    / "model_assumptions.csv"
)


required_files = [
    scenario_file,
    borrower_file,
    assumption_file
]

for file in required_files:

    if not file.exists():
        raise FileNotFoundError(
            f"Required input file missing:\n{file}"
        )


# ==================================================
# 3. Load datasets
# ==================================================

scenario = pd.read_csv(
    scenario_file
)

borrowers = pd.read_csv(
    borrower_file
)

assumptions = pd.read_csv(
    assumption_file
)


# ==================================================
# 4. Validation framework
# ==================================================

checks = []


def add_check(
    check_name,
    failures,
    severity="ERROR"
):

    failures = int(failures)

    checks.append(
        {
            "check_name": check_name,
            "severity": severity,
            "failures": failures,
            "status": (
                "PASS"
                if failures == 0
                else "FAIL"
            )
        }
    )


# ==================================================
# 5. Scenario checks
# ==================================================

add_check(
    "Scenario table contains 3 scenarios",
    len(scenario) != 3
)

add_check(
    "Scenario names are unique",
    scenario["scenario"]
    .duplicated()
    .sum()
)

add_check(
    "Scenario table has no missing values",
    scenario
    .isna()
    .sum()
    .sum()
)

add_check(
    "Price impact not below -100%",
    (
        scenario["price_impact"] < -1
    ).sum()
)

add_check(
    "Volume impact not below -100%",
    (
        scenario["volume_impact"] < -1
    ).sum()
)

add_check(
    "Additional OPEX non-negative",
    (
        scenario["additional_opex_pct"] < 0
    ).sum()
)

add_check(
    "Carbon price non-negative",
    (
        scenario["carbon_price"] < 0
    ).sum()
)

add_check(
    "Transition CAPEX non-negative",
    (
        scenario["transition_capex_pct"] < 0
    ).sum()
)


# ==================================================
# 6. Borrower checks
# ==================================================

add_check(
    "Borrower table contains 3 borrowers",
    len(borrowers) != 3
)

add_check(
    "Borrower names are unique",
    borrowers["borrower"]
    .duplicated()
    .sum()
)

add_check(
    "Borrower table has no missing values",
    borrowers
    .isna()
    .sum()
    .sum()
)

add_check(
    "Revenue is positive",
    (
        borrowers["revenue"] <= 0
    ).sum()
)

add_check(
    "EBITDA is positive",
    (
        borrowers["ebitda"] <= 0
    ).sum()
)

add_check(
    "Debt is non-negative",
    (
        borrowers["debt"] < 0
    ).sum()
)

add_check(
    "Cash is non-negative",
    (
        borrowers["cash"] < 0
    ).sum()
)

add_check(
    "Interest expense is non-negative",
    (
        borrowers["interest_expense"] < 0
    ).sum()
)

add_check(
    "Maintenance CAPEX is non-negative",
    (
        borrowers["maintenance_capex"] < 0
    ).sum()
)

add_check(
    "Scheduled principal is non-negative",
    (
        borrowers["scheduled_principal"] < 0
    ).sum()
)

add_check(
    "Emissions intensity is non-negative",
    (
        borrowers["emissions_intensity"] < 0
    ).sum()
)

add_check(
    "EAD is positive",
    (
        borrowers["ead"] <= 0
    ).sum()
)

add_check(
    "Baseline PD between 0 and 100%",
    (
        ~borrowers["baseline_pd"]
        .between(0, 1)
    ).sum()
)

add_check(
    "Baseline LGD between 0 and 100%",
    (
        ~borrowers["baseline_lgd"]
        .between(0, 1)
    ).sum()
)


# ==================================================
# 7. Assumption checks
# ==================================================

add_check(
    "Assumptions contain 3 rows",
    len(assumptions) != 3
)

add_check(
    "Assumption names are unique",
    assumptions["assumption"]
    .duplicated()
    .sum()
)

add_check(
    "Assumptions contain no missing values",
    assumptions
    .isna()
    .sum()
    .sum()
)


assumption_dict = dict(
    zip(
        assumptions["assumption"],
        assumptions["value"]
    )
)


required_assumptions = [
    "Cash tax rate on EBITDA",
    "PD cap",
    "LGD cap"
]


for item in required_assumptions:

    add_check(
        f"Required assumption exists: {item}",
        0 if item in assumption_dict else 1
    )


# ==================================================
# 8. Results
# ==================================================

validation_report = pd.DataFrame(
    checks
)

print("\nINPUT VALIDATION REPORT")
print("=" * 100)

print(
    validation_report.to_string(
        index=False
    )
)


# ==================================================
# 9. Export report
# ==================================================

validation_file = (
    PROCESSED_FOLDER
    / "input_validation_report.csv"
)

validation_report.to_csv(
    validation_file,
    index=False
)


# ==================================================
# 10. Overall status
# ==================================================

errors = validation_report[
    (
        validation_report["status"] == "FAIL"
    )
    &
    (
        validation_report["severity"] == "ERROR"
    )
]

print("\n" + "=" * 100)

if errors.empty:

    print(
        "PASS — All critical input controls passed."
    )

else:

    print(
        f"FAIL — {len(errors)} critical "
        f"input controls failed."
    )

    print(
        errors.to_string(
            index=False
        )
    )

print("\nValidation report exported:")
print(validation_file)


# Optional hard stop
if not errors.empty:
    raise ValueError(
        "Critical validation errors detected. "
        "Stress model should not run."
    )