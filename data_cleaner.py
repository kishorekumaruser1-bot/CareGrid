import pandas as pd
import numpy as np

# 1. Read the CSV file (using the path shown in your VS Code)
file_path = 'data/archivedatasets1/patients.csv'
print(f"Reading data from {file_path}...")
df = pd.read_csv(file_path)

# 2. Synthetically generate the required columns for the simulation
# Generating Severity Score (0-100)
df['Severity Score'] = np.random.randint(10, 95, size=len(df))

# Generating Survival Likelihood (0-100) based inversely on severity
df['Survival Likelihood'] = 100 - (df['Severity Score'] * 0.6) + np.random.normal(0, 5, size=len(df))
df['Survival Likelihood'] = df['Survival Likelihood'].clip(0, 100).round(2)

# Generating Baseline Waiting Time (in minutes)
df['Waiting Time'] = np.random.randint(5, 240, size=len(df))

# 3. Save the cleaned output
output_filename = 'cleaned_patients.csv'
df.to_csv(output_filename, index=False)
print(f"Success! Cleaned data saved to '{output_filename}'")