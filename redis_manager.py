import redis
import json

class RedisQueueManager:
    def __init__(self, host='localhost', port=6379, db=0):
        # decode_responses=True ensures we get strings back instead of bytes
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def update_bed_capacity(self, total: int, occupied: int):
        """Stores the bed capacity tracker."""
        self.client.hset(
            "bed_capacity", 
            mapping={
                "total": total, 
                "occupied": occupied
            }
        )

    def add_patient_to_active_queue(self, patient_json):
        """
        Adds a patient to the active waitlist. 
        Expects a dictionary or a JSON string containing a 'patient_id'.
        """
        if isinstance(patient_json, str):
            patient_data = json.loads(patient_json)
        else:
            patient_data = patient_json

        patient_id = patient_data.get("patient_id")
        
        if not patient_id:
            raise ValueError("The patient data must contain a 'patient_id' key.")

        # Store in a Redis Hash where the key is 'active_queue', field is patient_id, and value is the JSON string
        self.client.hset("active_queue", str(patient_id), json.dumps(patient_data))

    def get_entire_queue(self):
        """Retrieves the active waitlist as a list of dictionaries."""
        # Get all values from the 'active_queue' hash
        raw_patients = self.client.hvals("active_queue")
        
        # Parse the JSON strings back into Python dictionaries
        return [json.loads(patient_str) for patient_str in raw_patients]

    def remove_patient(self, patient_id):
        """Removes a patient from the queue when assigned a bed."""
        self.client.hdel("active_queue", str(patient_id))