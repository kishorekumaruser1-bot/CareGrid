import pandas as pd
import time
import requests

# Load the cleaned patient data
file_path = 'cleaned_patients.csv'
print(f"Loading data from {file_path}...")
df = pd.read_csv(file_path)

print("Starting live hospital simulation...")

# Loop through the data row by row
for index, row in df.iterrows():
    # Convert the single row to a JSON-compatible dictionary
    patient_data = row.to_dict()
    
    print(f"\n--- Sending Patient {index + 1} ---")
    print(f"Patient ID: {patient_data.get('patient_id', 'Unknown')}")
    
    try:
        # Send a POST request to the backend server
        response = requests.post('http://localhost:8000/api/new-patient', json=patient_data)
        print(f"Server Response: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Failed to connect. (This is normal if Member 2 hasn't started the backend server yet!)")
    
    # Wait 30 seconds before sending the next patient
    print("Waiting 30 seconds...")
    time.sleep(30)