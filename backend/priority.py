import math


# CareGrid configurable weights
W_SEVERITY = 0.5
W_SURVIVAL = 0.3
W_WAIT = 0.2


def normalize_severity(severity: float) -> float:
    """
    Convert clinical severity from 0-10 to 0-1.
    """
    return max(0.0, min(severity / 10.0, 1.0))


def survival_risk(survival_benefit: float) -> float:
    """
    CareGrid gives higher priority when ICU admission
    provides greater expected benefit.

    For the prototype scoring layer, we convert the
    supplied benefit value into a normalized risk/priority
    contribution.
    """
    return max(0.0, min(1.0 - survival_benefit, 1.0))


def wait_time_factor(waiting_time: float) -> float:
    """
    Saturating wait-time function.

    Waiting time matters increasingly at first, but
    should not dominate the score indefinitely.
    """
    return 1.0 - math.exp(-max(waiting_time, 0.0) / 8.0)


def calculate_priority(
    severity: float,
    survival_benefit: float,
    waiting_time: float
) -> float:

    severity_score = normalize_severity(severity)

    survival_score = survival_risk(survival_benefit)

    wait_score = wait_time_factor(waiting_time)

    score = (
        W_SEVERITY * severity_score
        + W_SURVIVAL * survival_score
        + W_WAIT * wait_score
    )

    return round(score, 4) 