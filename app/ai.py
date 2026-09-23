from app.models import PatientRecord


def compare_visits(patient: PatientRecord):

    if len(patient.visits) < 2:
        return {
            "error": "At least two visits are required for comparison."
        }

    # Sort visits by date
    visits = sorted(
        patient.visits,
        key=lambda visit: visit.date
    )

    previous_visit = visits[-2]
    latest_visit = visits[-1]

    changes = []

    # -----------------------------------
    # Compare laboratory results
    # -----------------------------------

    for latest_lab in latest_visit.lab_results:

        lab_found = False

        for previous_lab in previous_visit.lab_results:

            if latest_lab.name.lower() == previous_lab.name.lower():

                lab_found = True

                if latest_lab.value != previous_lab.value:

                    difference = (
                        latest_lab.value - previous_lab.value
                    )

                    changes.append({
                        "type": "lab_change",
                        "name": latest_lab.name,
                        "previous": previous_lab.value,
                        "current": latest_lab.value,
                        "difference": round(difference, 2),
                        "unit": latest_lab.unit
                    })

                break

        # Lab exists now but not in previous visit
        if not lab_found:

            changes.append({
                "type": "new_lab_result",
                "name": latest_lab.name,
                "previous": None,
                "current": latest_lab.value,
                "unit": latest_lab.unit
            })

    # -----------------------------------
    # Compare medications
    # -----------------------------------

    for latest_med in latest_visit.medications:

        medication_found = False

        for previous_med in previous_visit.medications:

            if latest_med.name.lower() == previous_med.name.lower():

                medication_found = True

                if latest_med.dosage != previous_med.dosage:

                    changes.append({
                        "type": "medication_change",
                        "name": latest_med.name,
                        "previous": previous_med.dosage,
                        "current": latest_med.dosage
                    })

                break

        # Medication exists now but not in previous visit
        if not medication_found:

            changes.append({
                "type": "new_medication",
                "name": latest_med.name,
                "previous": None,
                "current": latest_med.dosage
            })

    # -----------------------------------
    # Compare clinical notes
    # -----------------------------------

    previous_notes = [
        note.lower()
        for note in previous_visit.clinical_notes
    ]

    for latest_note in latest_visit.clinical_notes:

        latest_lower = latest_note.lower()

        # Exact match: nothing changed
        if latest_lower in previous_notes:
            continue

        # Look for related mentions of the same symptom
        related_note = None

        for previous_note in previous_notes:

            if "fatigue" in previous_note and "fatigue" in latest_lower:
                related_note = previous_note
                break

        if related_note:

            changes.append({
                "type": "clinical_note_change",
                "previous": related_note,
                "current": latest_note
            })

        else:

            changes.append({
                "type": "new_clinical_note",
                "previous": None,
                "current": latest_note
            })

    # -----------------------------------
    # Create human-readable summary
    # -----------------------------------

    summary = []

    for change in changes:

        if change["type"] == "lab_change":

            direction = (
                "increased"
                if change["difference"] > 0
                else "decreased"
            )

            summary.append(
                f'{change["name"]} {direction} from '
                f'{change["previous"]} {change["unit"]} to '
                f'{change["current"]} {change["unit"]} '
                f'({change["difference"]:+.2f} {change["unit"]}).'
            )

        elif change["type"] == "new_lab_result":

            summary.append(
                f'New lab result: '
                f'{change["name"]} = '
                f'{change["current"]} {change["unit"]}.'
            )

        elif change["type"] == "medication_change":

            summary.append(
                f'{change["name"]} dosage changed from '
                f'{change["previous"]} to '
                f'{change["current"]}.'
            )

        elif change["type"] == "new_medication":

            summary.append(
                f'New medication: '
                f'{change["name"]} at '
                f'{change["current"]}.'
            )

        elif change["type"] == "clinical_note_change":

            summary.append(
                f'Clinical note changed from '
                f'"{change["previous"]}" to '
                f'"{change["current"]}".'
            )

        elif change["type"] == "new_clinical_note":

            summary.append(
                f'New clinical note: '
                f'"{change["current"]}".'
            )

    return {
        "patient_id": patient.patient_id,
        "previous_visit": previous_visit.date,
        "latest_visit": latest_visit.date,
        "changes": changes,
        "summary": summary
    }
