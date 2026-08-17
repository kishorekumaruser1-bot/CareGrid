def calculate_cps(severity, survival_likelihood, waiting_time_mins, velocity_multiplier=1.0):
    """
    Calculate Composite Priority Score (CPS) from 0-100.
    
    Weights:
      - Severity: 45%
      - Survival Likelihood: 35%
      - Waiting Time Bonus: 20%
    
    severity: 0-100 scale
    survival_likelihood: 0-100 scale
    waiting_time_mins: minutes waited (caps bonus at 120+ mins)
    velocity_multiplier: if > 1.0, scales up severity before weighting
    """
    # Apply velocity multiplier to severity if applicable
    adjusted_severity = severity
    if velocity_multiplier > 1.0:
        adjusted_severity = min(severity * velocity_multiplier, 100)

    # Normalize waiting time (0-120+ mins -> 0-100 scale)
    normalized_wait = min(waiting_time_mins / 120.0, 1.0) * 100

    # Weighted components
    severity_component = adjusted_severity * 0.45
    survival_component = survival_likelihood * 0.35
    wait_component = normalized_wait * 0.20

    cps = severity_component + survival_component + wait_component

    # Clamp to 0-100
    cps = max(0, min(cps, 100))

    return round(cps, 2)


def check_velocity_multiplier(previous_severity, current_severity, time_delta_hours):
    """
    Determine if a velocity multiplier should be applied based on
    rapid severity escalation.
    
    If time_delta_hours <= 2 and severity increased by >= 15 points,
    return 1.25 (boosted priority). Otherwise return 1.0.
    """
    severity_jump = current_severity - previous_severity

    if time_delta_hours <= 2 and severity_jump >= 15:
        return 1.25

    return 1.0