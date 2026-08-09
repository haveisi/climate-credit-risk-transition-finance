from pathlib import Path
import pandas as pd


# ==================================================
# 1. Locate project folders
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Your project has previously shown a possible leading
# space in the data folder name, so support both.
DATA_FOLDER = PROJECT_ROOT / "data"

if not DATA_FOLDER.exists():
    DATA_FOLDER = PROJECT_ROOT / " data"

RAW_FOLDER = DATA_FOLDER / "raw"

print("=" * 100)
print("LOAD WORKBOOK")
print("=" * 100)

print("Project root:", PROJECT_ROOT)
print("Data folder:", DATA_FOLDER)
print("Raw folder:", RAW_FOLDER)


# ==================================================
# 2. Validate raw folder
# ==================================================

if not RAW_FOLDER.exists():
    raise FileNotFoundError(
        f"Raw folder not found:\n{RAW_FOLDER}"
    )


# ==================================================
# 3. Find Excel workbook
# ==================================================

excel_files = list(RAW_FOLDER.glob("*.xlsx"))

if len(excel_files) == 0:
    raise FileNotFoundError(
        f"No Excel workbook found in:\n{RAW_FOLDER}"
    )

if len(excel_files) > 1:
    print("\nWARNING: Multiple Excel files found.")

    for file in excel_files:
        print("-", file.name)

FILE_PATH = excel_files[0]

print("\nWorkbook selected:")
print(FILE_PATH)


# ==================================================
# 4. Load workbook
# ==================================================

excel_file = pd.ExcelFile(FILE_PATH)

print("\nWorkbook sheets:")
for i, sheet in enumerate(
    excel_file.sheet_names,
    start=1
):
    print(f"{i}. {sheet}")


# ==================================================
# 5. Create workbook inventory
# ==================================================

inventory = []

for sheet in excel_file.sheet_names:

    df = pd.read_excel(
        FILE_PATH,
        sheet_name=sheet,
        header=None
    )

    non_empty_rows = df.dropna(
        how="all"
    ).shape[0]

    non_empty_cols = df.dropna(
        axis=1,
        how="all"
    ).shape[1]

    inventory.append(
        {
            "sheet_name": sheet,
            "raw_rows": df.shape[0],
            "raw_columns": df.shape[1],
            "non_empty_rows": non_empty_rows,
            "non_empty_columns": non_empty_cols
        }
    )


inventory_df = pd.DataFrame(inventory)

print("\nWORKBOOK INVENTORY")
print("=" * 100)

print(
    inventory_df.to_string(
        index=False
    )
)


# ==================================================
# 6. Export inventory
# ==================================================

PROCESSED_FOLDER = DATA_FOLDER / "processed"

PROCESSED_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

inventory_file = (
    PROCESSED_FOLDER
    / "workbook_inventory.csv"
)

inventory_df.to_csv(
    inventory_file,
    index=False
)

print("\nWorkbook inventory exported:")
print(inventory_file)

print("\nLOAD COMPLETE")