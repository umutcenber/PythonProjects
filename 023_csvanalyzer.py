import pandas as pd
import os

print("=" * 40)
print("        CSV ANALYZER")
print("=" * 40)

file_path = input("Enter CSV file path: ").strip()

if not os.path.exists(file_path):
    print("❌ File not found.")
    exit()

try:
    df = pd.read_csv(file_path)

    print("\n📊 DATASET INFO")
    print("-" * 40)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumn Names:")
    for column in df.columns:
        print(f"- {column}")

    numeric_columns = df.select_dtypes(include="number")

    if not numeric_columns.empty:

        print("\nStatistics")

        for column in numeric_columns.columns:

            print(f"\n{column}")

            print(f"Average : {numeric_columns[column].mean():.2f}")
            print(f"Maximum : {numeric_columns[column].max()}")
            print(f"Minimum : {numeric_columns[column].min()}")

    else:
        print("\nNo numeric columns found.")

except Exception as e:
    print(f"\n❌ Error: {e}")