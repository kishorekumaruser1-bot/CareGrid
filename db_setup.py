import psycopg2

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"  # Default PostgreSQL database
DB_USER = "postgres"
DB_PASSWORD = "password123"


def setup_database():
    try:
        # Establish connection to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 1. Create Patients table for historical records
        create_patients_table = """
        CREATE TABLE IF NOT EXISTS Patients (
            patient_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            age INT,
            gender VARCHAR(20),
            admission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            severity_score FLOAT,
            survival_likelihood FLOAT,
            waiting_time_mins INT,
            status VARCHAR(50) DEFAULT 'Queued'
        );
        """

        # 2. Create Audit_Logs table with cryptographic hashing fields
        create_audit_logs_table = """
        CREATE TABLE IF NOT EXISTS Audit_Logs (
            log_id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_description TEXT NOT NULL,
            patient_id VARCHAR(50),
            composite_score FLOAT,
            previous_hash VARCHAR(64) NOT NULL,
            current_hash VARCHAR(64) NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES Patients(patient_id) ON DELETE SET NULL
        );
        """

        print("Connecting to PostgreSQL...")
        cursor.execute(create_patients_table)
        print("Table 'Patients' created successfully.")

        cursor.execute(create_audit_logs_table)
        print("Table 'Audit_Logs' created successfully.")

        cursor.close()
        conn.close()
        print("Database connection closed.")

    except Exception as e:
        print(f"Error during database setup: {e}")


if __name__ == "__main__":
    setup_database()