import psycopg2
import hashlib

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

def validate_audit_chain():
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Pull all rows from the 'Audit_Logs' table ordered by timestamp (and log_id to maintain exact sequence)
        cursor.execute("SELECT log_id, timestamp, event_description, patient_id, composite_score, previous_hash, current_hash FROM Audit_Logs ORDER BY log_id ASC;")
        rows = cursor.fetchall()

        if not rows:
            print("Audit log is empty. Nothing to validate.")
            return

        expected_previous_hash = "0" * 64  # The genesis hash used for the first entry

        for index, row in enumerate(rows):
            log_id, timestamp, event_description, patient_id, composite_score, previous_hash, current_hash = row

            # Format timestamp string consistently as it was stored/hashed during creation
            if hasattr(timestamp, 'strftime'):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = str(timestamp)

            # Recalculate the SHA-256 hash using the exact same data fields structure
            combined_string = f"{timestamp_str}|{event_description}|{patient_id}|{composite_score}|{previous_hash}"
            recalculated_hash = hashlib.sha256(combined_string.encode('utf-8')).hexdigest()

            # Check 1: Does the stored previous_hash match what it's supposed to be from the chain?
            if previous_hash != expected_previous_hash:
                print(f"\033[91mTAMPERING DETECTED at Log ID {log_id}: Previous hash mismatch!\033[0m")
                return

            # Check 2: Does the recalculated hash match the stored current_hash?
            if recalculated_hash != current_hash:
                print(f"\033[91mTAMPERING DETECTED at Log ID {log_id}: Current hash mismatch (Data altered)!\033[0m")
                return

            # Update expected previous_hash for the next iteration in the loop
            expected_previous_hash = current_hash

        print("\033[92mAudit Chain Validated: 100% Secure\033[0m")

    except Exception as e:
        print(f"Error during chain validation: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    validate_audit_chain()