import os
import pandas as pd

input_dir = "data"
output_dir = "csv_output"

# ✅ ONLY allowed folders
ALLOWED_FOLDERS = {"rain", "tmin", "tmax"}

os.makedirs(output_dir, exist_ok=True)

for root, dirs, files in os.walk(input_dir):

    # 🔥 extract top-level folder name after "data/"
    parts = root.split(os.sep)

    if len(parts) < 2:
        continue

    folder_name = parts[1]

    # ❌ SKIP realtime or anything else
    if folder_name not in ALLOWED_FOLDERS:
        print(f"Skipping folder: {folder_name}")
        continue

    for file in files:
        if file.endswith(".parquet"):

            parquet_path = os.path.join(root, file)
            print("Processing:", parquet_path)

            df = pd.read_parquet(parquet_path)

            relative_path = os.path.relpath(root, input_dir)
            save_dir = os.path.join(output_dir, relative_path)
            os.makedirs(save_dir, exist_ok=True)

            csv_path = os.path.join(
                save_dir,
                file.replace(".parquet", ".csv")
            )

            df.to_csv(csv_path, index=False)

print("DONE ✅ Only rain/tmin/tmax processed")
