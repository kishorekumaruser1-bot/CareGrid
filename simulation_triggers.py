import pandas as pd
import requests

def simulate_emergency_surge():
    # Read the cleaned data
    df = pd.read_csv('cleaned_patients.csv')
    
    # Filter for high severity (above 80)
    high_severity = df[df['Severity Score'] > 80]
    
    # Grab 5 random rows (using replace=True just in case there are fewer than 5 high severity patients)
    surge_patients = high_severity.sample(n=5, replace=True)
    
    # Convert to JSON (list of dictionaries)
    surge_data = surge_patients.to_dict(orient='records')
    
    # Send all 5 in a POST request
    try:
        response = requests.post('http://localhost:8000/api/surge', json=surge_data)
        print(f"Emergency surge sent! Server Response: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Failed to connect. (Member 2's backend server isn't running yet!)")

def simulate_edge_sensor():
    # Send an empty POST request
    try:
        response = requests.post('http://localhost:8000/api/bed-empty', json={})
        print("Simulated Edge AI weight sensor: Bed is now empty!")
    except requests.exceptions.ConnectionError:
        print("Failed to connect. (Member 2's backend server isn't running yet!)")

# You can uncomment the lines below to test them individually later
# simulate_emergency_surge()
# simulate_edge_sensor()