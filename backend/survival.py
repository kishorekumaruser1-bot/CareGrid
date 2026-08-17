def calculate_survival_benefit(patient):
    """
    Prototype survival-benefit estimator.

    IMPORTANT:
    This is NOT a clinical mortality model.
    It is used only for the CareGrid prototype/demo.
    """

    age = patient["age"]
    severity = patient["severity"]

    # Base benefit
    benefit = 0.85

    # Age adjustment
    if age < 40:
        benefit += 0.08
    elif age < 60:
        benefit += 0.04
    elif age < 75:
        benefit -= 0.02
    else:
        benefit -= 0.06

    # Severity adjustment
    # Moderate severity gives more potential benefit.
    if severity < 0.25:
        benefit -= 0.15
    elif severity < 0.50:
        benefit += 0.05
    elif severity < 0.75:
        benefit += 0.08
    else:
        benefit -= 0.03

    # Keep between 0 and 1
    benefit = max(0.0, min(1.0, benefit))

    return round(benefit, 4)