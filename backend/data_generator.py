import random


def generate_patient(patient_id):

    return {
        "patient_id": patient_id,

        "age": random.randint(20, 85),

        "pf_ratio": random.randint(80, 450),

        "platelets": random.randint(20, 250),

        "bilirubin": round(
            random.uniform(0.5, 12.0), 2
        ),

        "map": random.randint(50, 100),

        "vasopressor": random.choice([
            False,
            False,
            "low",
            "medium"
        ]),

        "gcs": random.randint(5, 15),

        "creatinine": round(
            random.uniform(0.5, 6.0), 2
        ),

        "wait_hours": round(
            random.uniform(0, 12), 2
        ),

        "trajectory": random.choice([
            "stable",
            "stable",
            "deteriorating"
        ]),

        "expected_los": random.randint(2, 15)
    }


def generate_patients(count=15):

    patients = []

    for i in range(count):

        patient_id = f"P-{i+1:03d}"

        patients.append(
            generate_patient(patient_id)
        )

    return patients