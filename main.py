from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from websocket_manager import ConnectionManager
from scoring import calculate_cps, check_velocity_multiplier
from queue_engine import rank_and_explain_queue

app = FastAPI()
manager = ConnectionManager()

# ---- In-memory state ----
active_queue: List[Dict[str, Any]] = []
total_beds = 10
occupied_beds = 10


# ---- Request models ----
class PatientIn(BaseModel):
    id: str
    severity: float
    survival_likelihood: float
    waiting_time_mins: float
    previous_severity: float = None
    time_delta_hours: float = None


class SurgeIn(BaseModel):
    patients: List[PatientIn]


# ---- Helpers ----
def build_patient_record(patient: PatientIn) -> Dict[str, Any]:
    velocity_multiplier = 1.0
    if patient.previous_severity is not None and patient.time_delta_hours is not None:
        velocity_multiplier = check_velocity_multiplier(
            patient.previous_severity,
            patient.severity,
            patient.time_delta_hours,
        )

    cps = calculate_cps(
        severity=patient.severity,
        survival_likelihood=patient.survival_likelihood,
        waiting_time_mins=patient.waiting_time_mins,
        velocity_multiplier=velocity_multiplier,
    )

    return {
        "ID": patient.id,
        "CPS": cps,
        "Severity": patient.severity,
        "Survival Likelihood": patient.survival_likelihood,
        "Waiting Time": patient.waiting_time_mins,
        "Velocity Multiplier": velocity_multiplier,
    }


def get_available_beds() -> int:
    return total_beds - occupied_beds


# ---- WebSocket endpoint ----
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; ignore inbound messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---- New patient endpoint ----
@app.post("/api/new-patient")
async def new_patient(patient: PatientIn):
    record = build_patient_record(patient)
    active_queue.append(record)

    ranked_queue = rank_and_explain_queue(active_queue)
    active_queue.clear()
    active_queue.extend(ranked_queue)

    await manager.broadcast({"queue": active_queue})

    response = {"queue": active_queue}

    available_beds = get_available_beds()
    if available_beds == 0:
        response["warning"] = (
            "Local ICU Exhausted: Route Patient to Sister Hospital B "
            "(3.2 miles away, 2 beds available)"
        )

    return response


# ---- Surge endpoint ----
@app.post("/api/surge")
async def surge(surge_in: SurgeIn):
    for patient in surge_in.patients:
        record = build_patient_record(patient)
        active_queue.append(record)

    ranked_queue = rank_and_explain_queue(active_queue)
    active_queue.clear()
    active_queue.extend(ranked_queue)

    await manager.broadcast({"queue": active_queue})

    response = {"queue": active_queue}

    available_beds = get_available_beds()
    if available_beds == 0:
        response["warning"] = (
            "Local ICU Exhausted: Route Patient to Sister Hospital B "
            "(3.2 miles away, 2 beds available)"
        )

    return response


# ---- Bed empty endpoint (Edge AI sensor) ----
@app.post("/api/bed-empty")
async def bed_empty():
    global occupied_beds

    if occupied_beds > 0:
        occupied_beds -= 1

    if active_queue:
        active_queue.pop(0)

    ranked_queue = rank_and_explain_queue(active_queue)
    active_queue.clear()
    active_queue.extend(ranked_queue)

    await manager.broadcast({"queue": active_queue})

    return {
        "occupied_beds": occupied_beds,
        "available_beds": get_available_beds(),
        "queue": active_queue,
    }