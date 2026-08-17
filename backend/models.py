from pydantic import BaseModel, Field


class Patient(BaseModel):
    # -------------------------
    # BASIC PATIENT INFORMATION
    # -------------------------

    name: str
    age: int = Field(ge=0)

    condition: str = ""

    # -------------------------
    # CLINICAL DATA
    # Used by severity.py
    # -------------------------

    pf_ratio: float = Field(ge=0)
    platelets: float = Field(ge=0)
    bilirubin: float = Field(ge=0)
    map: float
    vasopressor: str = "none"
    gcs: int = Field(ge=3, le=15)
    creatinine: float = Field(ge=0)

    # -------------------------
    # WAITING TIME
    # -------------------------

    wait_hours: float = Field(
        default=0,
        ge=0
    )

    # -------------------------
    # RANKING / TIE-BREAKERS
    # -------------------------

    condition_trajectory: str = "stable"

    expected_los: float = Field(
        default=0,
        ge=0
    )

    clinician_escalated: bool = False


class Bed(BaseModel):
    bed_id: str
    icu: bool
    occupied: bool