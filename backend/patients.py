from ranking import rank_patients


# In-memory patient store
patients = []


def add_patient(patient):
    """
    Add a patient to the current ICU queue.

    The patient is converted to a dictionary because
    the ranking pipeline works with dictionary-based
    patient records.
    """

    patient_data = patient.model_dump()

    patients.append(patient_data)

    return patient_data


def get_ranked_patients():
    """
    Process and rank all patients using the primary
    CareGrid ranking pipeline.
    """

    if not patients:
        return []

    # Work on copies so ranking does not unexpectedly
    # modify the stored patient records.
    patient_records = [
        patient.copy()
        for patient in patients
    ]

    return rank_patients(patient_records)