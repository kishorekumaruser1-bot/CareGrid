def calculate_severity(patient):
    """
    Calculates a normalized severity score from 0 to 1.

    Higher value = greater physiological severity.

    Prototype implementation inspired by SOFA-style
    organ dysfunction scoring.
    """

    scores = []

    # -------------------------
    # RESPIRATION
    # -------------------------

    pf_ratio = patient["pf_ratio"]

    if pf_ratio >= 400:
        respiratory = 0
    elif pf_ratio >= 300:
        respiratory = 1
    elif pf_ratio >= 200:
        respiratory = 2
    elif pf_ratio >= 100:
        respiratory = 3
    else:
        respiratory = 4

    scores.append(respiratory)

    # -------------------------
    # COAGULATION
    # -------------------------

    platelets = patient["platelets"]

    if platelets >= 150:
        coagulation = 0
    elif platelets >= 100:
        coagulation = 1
    elif platelets >= 50:
        coagulation = 2
    elif platelets >= 20:
        coagulation = 3
    else:
        coagulation = 4

    scores.append(coagulation)

    # -------------------------
    # LIVER
    # -------------------------

    bilirubin = patient["bilirubin"]

    if bilirubin < 1.2:
        liver = 0
    elif bilirubin < 2.0:
        liver = 1
    elif bilirubin < 6.0:
        liver = 2
    elif bilirubin < 12.0:
        liver = 3
    else:
        liver = 4

    scores.append(liver)

    # -------------------------
    # CARDIOVASCULAR
    # -------------------------

    map_value = patient["map"]
    vasopressor = patient["vasopressor"]

    if map_value >= 70 and not vasopressor:
        cardiovascular = 0
    elif map_value < 70 and not vasopressor:
        cardiovascular = 1
    elif vasopressor == "low":
        cardiovascular = 2
    elif vasopressor == "medium":
        cardiovascular = 3
    else:
        cardiovascular = 4

    scores.append(cardiovascular)

    # -------------------------
    # CNS / GCS
    # -------------------------

    gcs = patient["gcs"]

    if gcs >= 15:
        cns = 0
    elif gcs >= 13:
        cns = 1
    elif gcs >= 10:
        cns = 2
    elif gcs >= 6:
        cns = 3
    else:
        cns = 4

    scores.append(cns)

    # -------------------------
    # RENAL
    # -------------------------

    creatinine = patient["creatinine"]

    if creatinine < 1.2:
        renal = 0
    elif creatinine < 2.0:
        renal = 1
    elif creatinine < 3.5:
        renal = 2
    elif creatinine < 5.0:
        renal = 3
    else:
        renal = 4

    scores.append(renal)

    # -------------------------
    # TOTAL SOFA STYLE SCORE
    # -------------------------

    total_score = sum(scores)

    # Maximum = 24
    normalized = total_score / 24

    return {
        "organ_scores": scores,
        "severity_raw": total_score,
        "severity": round(normalized, 4)
    }