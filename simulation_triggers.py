import pandas as pd
import requests

def simulate_emergency_surge():
    # Read the cleaned data
    df = pd.read_csv('cleaned_patients.csv')
    
    # Filter for high severity (above 80)
    high_severity = df[df['Severity Score'] > 80]
    
    # Grab 5 random rows (using replace=True just in case there are fewer than 5 high severity patients)
    surge_patients = high_severity.sample(n=5, replace=True)
    
    # Map CSV columns to match Member 2's FastAPI PatientIn schema precisely
    formatted_patients = []
    for _, row in surge_patients.iterrows():
        formatted_patients.append({
            "id": str(row.get('Patient_ID', row.get('id', 'P-UNKNOWN'))),
            "severity": float(row.get('Severity Score', row.get('severity', 0))),
            "survival_likelihood": float(row.get('Survival Likelihood', row.get('survival_likelihood', 0))),
            "waiting_time_mins": float(row.get('Waiting Time Mins', row.get('waiting_time_mins', 0))),
            "previous_severity": float(row.get('Previous Severity')) if pd.notna(row.get('Previous Severity')) else None,
            "time_delta_hours": float(row.get('Time Delta Hours')) if pd.notna(row.get('Time Delta Hours')) else None
        })
    
    # Member 2's backend /api/surge endpoint expects {"patients": [...]}, NOT just a raw list
    payload = {"patients": formatted_patients}
    
    # Send all 5 in a POST request
    try:
        response = requests.post('http://localhost:8000/api/surge', json=payload)
        print(f"Emergency surge sent! Server Response: {response.status_code}")
        print(response.json())
    except requests.exceptions.ConnectionError:
        print("Failed to connect. (Member 2's backend server isn't running yet!)")

def simulate_edge_sensor():
    # Send an empty POST request
    try:
        response = requests.post('http://localhost:8000/api/bed-empty', json={})
        print("Simulated Edge AI weight sensor: Bed is now empty!")
        print(response.json())
    except requests.exceptions.ConnectionError:
        print("Failed to connect. (Member 2's backend server isn't running yet!)")

if __name__ == "__main__":
    # You can uncomment these to test them directly when running the script
    # simulate_emergency_surge()
    # simulate_edge_sensor()
    pass