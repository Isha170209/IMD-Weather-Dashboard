import os
import pandas as pd

input_dir = "data"
output_dir = "csv_output"

CHUNK_SIZE = 200000   # adjust (try 100k–300k rows depending on dataset)

os.makedirs(output_dir, exist_ok=True)

for root, dirs, files in os.walk(input_dir):
    for file in files:
        if file.endswith(".parquet"):

            parquet_path = os.path.join(root, file)
            print("Processing:", parquet_path)

            df = pd.read_parquet(parquet_path)

            relative_path = os.path.relpath(root, input_dir)
            save_dir = os.path.join(output_dir, relative_path)
            os.makedirs(save_dir, exist_ok=True)

            base_name = file.replace(".parquet", "")

            # 🔥 CHUNKING START
            total_rows = len(df)
            num_chunks = (total_rows // CHUNK_SIZE) + 1

            for i in range(num_chunks):
                start = i * CHUNK_SIZE
                end = start + CHUNK_SIZE

                chunk = df.iloc[start:end]

                if chunk.empty:
                    continue

                csv_path = os.path.join(
                    save_dir,
                    f"{base_name}_part{i+1}.csv"
                )

                chunk.to_csv(csv_path, index=False)

                print(f"Saved chunk: {csv_path}")

print("DONE ✅ All files chunked safely")
