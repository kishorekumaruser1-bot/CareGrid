from fastapi import FastAPI

from models import Patient
from priority import calculate_priority
from patients import add_patient, get_ranked_patients

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "ICU Bed Priority System is running"
    }


@app.post("/priority")
def get_priority(patient: Patient):

    score = calculate_priority(
    patient.severity,
    patient.survival_benefit,
    patient.waiting_time
)

    return {
        "patient": patient.name,
        "priority_score": score
    }


@app.post("/patients")
def create_patient(patient: Patient):

    add_patient(patient)

    return {
        "message": "Patient added successfully",
        "patient": patient.name
    }


@app.get("/patients")
def ranked_patients():

    return get_ranked_patients()