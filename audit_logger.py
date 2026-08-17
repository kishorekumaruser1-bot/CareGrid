import psycopg2
import hashlib
from datetime import datetime

# Database connection parameters (matching your previous setup)
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"  
DB_USER = "postgres"
DB_PASSWORD = "password123"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

def create_secure_log(event_description, patient_id, score):
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch the current_hash of the most recent log entry
        cursor.execute("SELECT current_hash FROM Audit_Logs ORDER BY log_id DESC LIMIT 1;")
        result = cursor.fetchone()
        
        # If there is a previous log, use its hash. Otherwise, use a genesis hash (e.g., 64 zeros).
        previous_hash = result[0] if result else "0" * 64

        # Get current timestamp and format it as a string for hashing consistency
        current_timestamp = datetime.now()
        timestamp_str = current_timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # 2. Create a combined string of all the data elements
        combined_string = f"{timestamp_str}|{event_description}|{patient_id}|{score}|{previous_hash}"

        # 3. Apply a SHA-256 cryptographic hash to the combined string
        current_hash = hashlib.sha256(combined_string.encode('utf-8')).hexdigest()

        # 4. Insert the new log entry, including previous_hash and current_hash
        insert_query = """
            INSERT INTO Audit_Logs 
            (timestamp, event_description, patient_id, composite_score, previous_hash, current_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_query, 
            (current_timestamp, event_description, patient_id, score, previous_hash, current_hash)
        )
        
        # Commit the transaction to save it to the database
        conn.commit()
        print(f"Secure log created for Patient {patient_id}. Hash: {current_hash[:8]}...")

    except Exception as e:
        print(f"Error creating secure log: {e}")
        if conn:
            conn.rollback()  # Rollback on error to prevent database corruption
    finally:
        # Always ensure the database connection is properly closed
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Example Usage:
if __name__ == "__main__":
    create_secure_log("Patient #104 entered queue", "104", 72.1)
    create_secure_log("Tie-breaker invoked; wait time priority given", "105", 84.5)