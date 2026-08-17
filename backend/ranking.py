from severity import calculate_severity
from survival import calculate_survival_benefit
from scoring import (
    calculate_wait_factor,
    calculate_priority_score
)


# Small band used to detect near-ties
EPSILON = 0.02


def process_patient(patient):

    # -------------------------
    # 1. Calculate severity
    # -------------------------

    severity_result = calculate_severity(patient)

    patient["severity_raw"] = severity_result["severity_raw"]
    patient["severity"] = severity_result["severity"]

    # -------------------------
    # 2. Calculate survival benefit
    # -------------------------

    patient["survival_benefit"] = calculate_survival_benefit(patient)

    # -------------------------
    # 3. Calculate wait factor
    # -------------------------

    patient["wait_factor"] = calculate_wait_factor(
        patient["wait_hours"]
    )

    # -------------------------
    # 4. Calculate priority score
    # -------------------------

    patient["priority_score"] = calculate_priority_score(
        severity=patient["severity"],
        survival_benefit=patient["survival_benefit"],
        wait_factor=patient["wait_factor"]
    )

    return patient


def deterioration_value(patient):
    """
    Higher value means the patient's condition
    is deteriorating and therefore gets tie-break priority.
    """

    trajectory = str(
        patient.get("condition_trajectory", "stable")
    ).lower()

    if trajectory == "deteriorating":
        return 2

    if trajectory == "stable":
        return 1

    if trajectory == "improving":
        return 0

    return 1


def clinician_escalation_value(patient):
    """
    Clinician escalation is the final tie-breaker.
    """

    if patient.get("clinician_escalated", False):
        return 1

    return 0


def rank_patients(patients):

    # -------------------------
    # STEP 1: Process patients
    # -------------------------

    processed = []

    for patient in patients:

        processed.append(
            process_patient(patient)
        )

    # -------------------------
    # STEP 2: Primary ranking
    # -------------------------

    processed.sort(
        key=lambda x: x["priority_score"],
        reverse=True
    )

    # -------------------------
    # STEP 3: Deterministic
    #         tie-breaking
    # -------------------------

    i = 0

    while i < len(processed):

        current_score = processed[i]["priority_score"]

        tie_group = [processed[i]]

        j = i + 1

        while j < len(processed):

            next_score = processed[j]["priority_score"]

            if abs(current_score - next_score) <= EPSILON:
                tie_group.append(processed[j])
                j += 1
            else:
                break

        # If there is a near-tie
        if len(tie_group) > 1:

            tie_group.sort(
                key=lambda patient: (
                    # 1. Deteriorating condition
                    deterioration_value(patient),

                    # 2. Longer accumulated waiting time
                    patient.get("wait_hours", 0),

                    # 3. Expected LOS / reversibility proxy
                    # Lower LOS gets preference
                    -patient.get("expected_los", 0),

                    # 4. Clinician escalation
                    clinician_escalation_value(patient)
                ),
                reverse=True
            )

            processed[i:j] = tie_group

        i = j

    # -------------------------
    # STEP 4: Assign final rank
    # -------------------------

    for index, patient in enumerate(
        processed,
        start=1
    ):

        patient["rank"] = index

        # -------------------------
        # Explain why the patient
        # received this ranking
        # -------------------------

        reasons = []

        if patient["severity"] >= 0.7:
            reasons.append(
                "High clinical severity"
            )

        if patient["survival_benefit"] >= 0.7:
            reasons.append(
                "High expected ICU benefit"
            )

        if patient.get("wait_hours", 0) > 4:
            reasons.append(
                "Long accumulated waiting time"
            )

        if patient.get("condition_trajectory") == "deteriorating":
            reasons.append(
                "Condition is deteriorating"
            )

        if patient.get("clinician_escalated", False):
            reasons.append(
                "Clinician escalation recorded"
            )

        if not reasons:
            reasons.append(
                "Priority determined by composite score"
            )

        patient["rank_reasons"] = reasons

    return processed