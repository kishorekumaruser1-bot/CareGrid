def tie_breaker(patient_a, patient_b):

    # --------------------------------
    # RULE 1: CONDITION TRAJECTORY
    # --------------------------------

    if patient_a["trajectory"] != patient_b["trajectory"]:

        if patient_a["trajectory"] == "deteriorating":
            return patient_a, "Condition trajectory"

        if patient_b["trajectory"] == "deteriorating":
            return patient_b, "Condition trajectory"

    # --------------------------------
    # RULE 2: ACCUMULATED WAIT
    # --------------------------------

    if patient_a["wait_hours"] != patient_b["wait_hours"]:

        if patient_a["wait_hours"] > patient_b["wait_hours"]:
            return patient_a, "Accumulated wait"

        return patient_b, "Accumulated wait"

    # --------------------------------
    # RULE 3: EXPECTED LOS
    # --------------------------------

    if patient_a["expected_los"] != patient_b["expected_los"]:

        if patient_a["expected_los"] < patient_b["expected_los"]:
            return patient_a, "Expected reversibility"

        return patient_b, "Expected reversibility"

    # --------------------------------
    # RULE 4: HUMAN REVIEW
    # --------------------------------

    return None, "Clinician review required"