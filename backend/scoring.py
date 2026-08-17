import math


# -----------------------------------
# WAIT TIME
# -----------------------------------

def calculate_wait_factor(wait_hours):
    """
    Saturating logarithmic wait-time function.

    Wait time contributes more initially,
    but does not dominate the priority score indefinitely.

    Output:
        0 to 1
    """

    wait_hours = max(0.0, float(wait_hours))

    factor = math.log1p(wait_hours) / math.log1p(24)

    return round(min(1.0, factor), 4)


# -----------------------------------
# COMPOSITE PRIORITY SCORE
# -----------------------------------

def calculate_priority_score(
    severity,
    survival_benefit,
    wait_factor,
    w1=0.5,
    w2=0.3,
    w3=0.2
):
    """
    CareGrid composite priority score.

    Priority =
        w1 * Severity
        + w2 * (1 - Survival Benefit)
        + w3 * Wait Factor

    All components are expected to be normalized
    between 0 and 1.

    Output:
        Priority score between 0 and 1.
    """

    # -------------------------------
    # Validate weights
    # -------------------------------

    if abs((w1 + w2 + w3) - 1.0) > 0.001:
        raise ValueError(
            "Weights must sum to 1"
        )

    # -------------------------------
    # Validate input ranges
    # -------------------------------

    severity = max(
        0.0,
        min(float(severity), 1.0)
    )

    survival_benefit = max(
        0.0,
        min(float(survival_benefit), 1.0)
    )

    wait_factor = max(
        0.0,
        min(float(wait_factor), 1.0)
    )

    # -------------------------------
    # Composite score
    # -------------------------------

    priority = (
        w1 * severity
        + w2 * (1.0 - survival_benefit)
        + w3 * wait_factor
    )

    return round(
        max(0.0, min(priority, 1.0)),
        4
    )