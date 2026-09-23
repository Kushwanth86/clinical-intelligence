from app.models import PatientRecord


def compare_visits(patient: PatientRecord):
    if len(patient.visits) < 2:
        raise ValueError("At least two visits are required for comparison.")

    visits = sorted(patient.visits, key=lambda visit: visit.date)
    previous_visit = visits[-2]
    latest_visit = visits[-1]
    changes = []

    for latest_lab in latest_visit.lab_results:
        lab_found = False

        for previous_lab in previous_visit.lab_results:
            if latest_lab.name.lower() == previous_lab.name.lower():
                lab_found = True

                if latest_lab.value != previous_lab.value:
                    difference = latest_lab.value - previous_lab.value

                    changes.append({
                        "type": "lab_change",
                        "name": latest_lab.name,
                        "previous": previous_lab.value,
                        "current": latest_lab.value,
                        "difference": round(difference, 2),
                        "unit": latest_lab.unit
                    })

                break

        if not lab_found:
            changes.append({
                "type": "new_lab_result",
                "name": latest_lab.name,
                "previous": None,
                "current": latest_lab.value,
                "unit": latest_lab.unit
            })

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

        if not medication_found:
            changes.append({
                "type": "new_medication",
                "name": latest_med.name,
                "previous": None,
                "current": latest_med.dosage
            })

    previous_notes = [note.lower() for note in previous_visit.clinical_notes]

    for latest_note in latest_visit.clinical_notes:
        latest_lower = latest_note.lower()

        if latest_lower in previous_notes:
            continue

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

    summary = []

    for change in changes:
        if change["type"] == "lab_change":
            direction = "increased" if change["difference"] > 0 else "decreased"
            summary.append(
                f'{change["name"]} {direction} from '
                f'{change["previous"]} {change["unit"]} to '
                f'{change["current"]} {change["unit"]} '
                f'({change["difference"]:+.2f} {change["unit"]}).'
            )

        elif change["type"] == "new_lab_result":
            summary.append(
                f'New lab result: {change["name"]} = '
                f'{change["current"]} {change["unit"]}.'
            )

        elif change["type"] == "medication_change":
            summary.append(
                f'{change["name"]} dosage changed from '
                f'{change["previous"]} to {change["current"]}.'
            )

        elif change["type"] == "new_medication":
            summary.append(
                f'New medication: {change["name"]} at {change["current"]}.'
            )

        elif change["type"] == "clinical_note_change":
            summary.append(
                f'Clinical note changed from '
                f'"{change["previous"]}" to "{change["current"]}".'
            )

        elif change["type"] == "new_clinical_note":
            summary.append(
                f'New clinical note: "{change["current"]}".'
            )

    return {
        "patient_id": patient.patient_id,
        "previous_visit": previous_visit.date,
        "latest_visit": latest_visit.date,
        "changes": changes,
        "summary": summary
    }


def answer_question(patient: PatientRecord, question: str):
    if not patient.visits:
        return {
            "question": question,
            "answer": "No visits are available for this patient.",
            "evidence": []
        }

    visits = sorted(patient.visits, key=lambda visit: visit.date)
    latest = visits[-1]
    q = question.lower()
    evidence = []

    if "medication" in q or "medicine" in q or "taking" in q:
        medications = latest.medications

        if not medications:
            answer = f"No medications are documented at the latest visit ({latest.date})."
        else:
            items = []

            for medication in medications:
                items.append(f"{medication.name} ({medication.dosage})")
                evidence.append({
                    "visit_date": latest.date,
                    "source_type": "medication",
                    "content": f"{medication.name} - {medication.dosage}"
                })

            answer = (
                f"Medications documented at the latest visit ({latest.date}): "
                + ", ".join(items) + "."
            )

    elif "hba1c" in q:
        results = []

        for visit in visits:
            for lab in visit.lab_results:
                if lab.name.lower() == "hba1c":
                    results.append((visit.date, lab.value, lab.unit))
                    evidence.append({
                        "visit_date": visit.date,
                        "source_type": "lab_result",
                        "content": f"HbA1c: {lab.value} {lab.unit}"
                    })

        if not results:
            answer = "No HbA1c results are documented."
        elif len(results) == 1:
            date, value, unit = results[0]
            answer = f"HbA1c was {value} {unit} on {date}."
        else:
            first = results[0]
            last = results[-1]
            difference = last[1] - first[1]
            answer = (
                f"HbA1c was {first[1]} {first[2]} on {first[0]} and "
                f"{last[1]} {last[2]} on {last[0]}. "
                f"The recorded difference is {difference:+.2f} {last[2]}."
            )

    elif "history" in q or "medical history" in q:
        history = patient.medical_history

        if history:
            answer = "Medical history: " + ", ".join(history) + "."

            for item in history:
                evidence.append({
                    "visit_date": "patient history",
                    "source_type": "medical_history",
                    "content": item
                })
        else:
            answer = "No medical history is documented."

    else:
        answer = (
            "I can currently answer questions about medications, HbA1c, "
            "and medical history from the structured patient record."
        )

    return {
        "question": question,
        "answer": answer,
        "evidence": evidence
    }
