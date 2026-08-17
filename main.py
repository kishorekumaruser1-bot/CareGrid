from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from websocket_manager import ConnectionManager
from scoring import calculate_cps, check_velocity_multiplier
from queue_engine import rank_and_explain_queue

# ---- Member 3 Imports (Redis & Secure Audit Logs) ----
from redis_manager import RedisQueueManager
from audit_logger import create_secure_log

app = FastAPI()
manager = ConnectionManager()
redis_queue = RedisQueueManager()

# ---- In-memory state tracking for beds ----
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
        "patient_id": patient.id,  # Kept consistent with Redis keys
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
    
    # 1. Add/Update patient in Redis
    redis_queue.add_patient_to_active_queue(record)

    # 2. Fetch entire queue from Redis, rank, and re-save/sort
    raw_queue = redis_queue.get_entire_queue()
    ranked_queue = rank_and_explain_queue(raw_queue)
    
    # Re-sync sorted order into Redis
    for p in ranked_queue:
        redis_queue.add_patient_to_active_queue(p)

    active_queue = ranked_queue
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
        redis_queue.add_patient_to_active_queue(record)

    raw_queue = redis_queue.get_entire_queue()
    ranked_queue = rank_and_explain_queue(raw_queue)

    for p in ranked_queue:
        redis_queue.add_patient_to_active_queue(p)

    active_queue = ranked_queue
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

    # Fetch current queue from Redis to pop the top priority patient
    raw_queue = redis_queue.get_entire_queue()
    ranked_queue = rank_and_explain_queue(raw_queue)

    if ranked_queue:
        top_patient = ranked_queue.pop(0)
        patient_id = top_patient.get("patient_id") or top_patient.get("ID")
        composite_score = top_patient.get("CPS", 0.0)

        # 1. Remove from Redis database
        redis_queue.remove_patient(patient_id)

        # 2. Securely log this state change with SHA-256 in PostgreSQL
        create_secure_log(
            event_description="Patient assigned bed and removed from queue",
            patient_id=str(patient_id),
            score=float(composite_score)
        )

    # Re-rank remaining queue
    remaining_raw = redis_queue.get_entire_queue()
    active_queue = rank_and_explain_queue(remaining_raw)

    await manager.broadcast({"queue": active_queue})

    return {
        "occupied_beds": occupied_beds,
        "available_beds": get_available_beds(),
        "queue": active_queue,
    }