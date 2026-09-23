from app.models import PatientRecord


# ==========================================================
# COMPARE VISITS
# ==========================================================

def compare_visits(patient: PatientRecord):

    if len(patient.visits) < 2:
        raise ValueError(
            "At least two visits are required for comparison."
        )

    # Sort visits chronologically
    visits = sorted(
        patient.visits,
        key=lambda visit: visit.date
    )

    previous_visit = visits[-2]
    latest_visit = visits[-1]

    changes = []

    # ------------------------------------------------------
    # Compare laboratory results
    # ------------------------------------------------------

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

        # New lab result
        if not lab_found:

            changes.append({
                "type": "new_lab_result",
                "name": latest_lab.name,
                "previous": None,
                "current": latest_lab.value,
                "difference": None,
                "unit": latest_lab.unit
            })

    # ------------------------------------------------------
    # Compare medications
    # ------------------------------------------------------

    for latest_med in latest_visit.medications:

        medication_found = False

        for previous_med in previous_visit.medications:

            if latest_med.name.lower() == previous_med.name.lower():

                medication_found = True

                # Dosage changed
                if latest_med.dosage != previous_med.dosage:

                    changes.append({
                        "type": "medication_change",
                        "name": latest_med.name,
                        "previous": previous_med.dosage,
                        "current": latest_med.dosage,
                        "difference": None,
                        "unit": None
                    })

                break

        # New medication
        if not medication_found:

            changes.append({
                "type": "new_medication",
                "name": latest_med.name,
                "previous": None,
                "current": latest_med.dosage,
                "difference": None,
                "unit": None
            })

    # ------------------------------------------------------
    # Compare clinical notes
    # ------------------------------------------------------

    previous_notes = [
        note.lower()
        for note in previous_visit.clinical_notes
    ]

    for latest_note in latest_visit.clinical_notes:

        latest_lower = latest_note.lower()

        # Exact match
        if latest_lower in previous_notes:
            continue

        related_note = None

        # Simple semantic relationship
        for previous_note in previous_notes:

            if (
                "fatigue" in previous_note
                and "fatigue" in latest_lower
            ):
                related_note = previous_note
                break

        if related_note:

            changes.append({
                "type": "clinical_note_change",
                "name": None,
                "previous": related_note,
                "current": latest_note,
                "difference": None,
                "unit": None
            })

        else:

            changes.append({
                "type": "new_clinical_note",
                "name": None,
                "previous": None,
                "current": latest_note,
                "difference": None,
                "unit": None
            })

    # ------------------------------------------------------
    # Human-readable summary
    # ------------------------------------------------------

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
                f'{change["current"]} '
                f'{change["unit"]}.'
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


# ==========================================================
# PATIENT QUESTION ANSWERING
# ==========================================================

def answer_question(
    patient: PatientRecord,
    question: str
):

    if not patient.visits:

        return {
            "question": question,
            "answer": "No visits are available for this patient.",
            "evidence": []
        }

    # Sort visits chronologically
    visits = sorted(
        patient.visits,
        key=lambda visit: visit.date
    )

    latest = visits[-1]

    q = question.lower().strip()

    evidence = []

    # ======================================================
    # MEDICATION QUESTIONS
    # ======================================================

    if (
        "medication" in q
        or "medications" in q
        or "medicine" in q
        or "medicines" in q
        or "taking" in q
    ):

        medications = latest.medications

        if not medications:

            answer = (
                f"No medications are documented "
                f"at the latest visit ({latest.date})."
            )

        else:

            items = []

            for medication in medications:

                items.append(
                    f"{medication.name} "
                    f"({medication.dosage})"
                )

                evidence.append({
                    "visit_date": latest.date,
                    "source_type": "medication",
                    "content": (
                        f"{medication.name} - "
                        f"{medication.dosage}"
                    )
                })

            answer = (
                f"Medications documented at the latest visit "
                f"({latest.date}): "
                + ", ".join(items)
                + "."
            )

    # ======================================================
    # LATEST LABORATORY RESULTS
    # ======================================================

    elif (
        "laboratory" in q
        or "lab results" in q
        or "lab result" in q
        or "latest labs" in q
        or "latest laboratory" in q
    ):

        labs = latest.lab_results

        if not labs:

            answer = (
                f"No laboratory results are documented "
                f"at the latest visit ({latest.date})."
            )

        else:

            items = []

            for lab in labs:

                items.append(
                    f"{lab.name} "
                    f"({lab.value} {lab.unit})"
                )

                evidence.append({
                    "visit_date": latest.date,
                    "source_type": "lab_result",
                    "content": (
                        f"{lab.name}: "
                        f"{lab.value} "
                        f"{lab.unit}"
                    )
                })

            answer = (
                f"Laboratory results documented at the latest "
                f"visit ({latest.date}): "
                + ", ".join(items)
                + "."
            )

    # ======================================================
    # CLINICAL NOTE QUESTIONS
    # ======================================================

    elif (
        "clinical note" in q
        or "clinical notes" in q
        or "notes" in q
        or "symptoms documented" in q
    ):

        notes = latest.clinical_notes

        if not notes:

            answer = (
                f"No clinical notes are documented "
                f"at the latest visit ({latest.date})."
            )

        else:

            for note in notes:

                evidence.append({
                    "visit_date": latest.date,
                    "source_type": "clinical_note",
                    "content": note
                })

            answer = (
                f"Clinical notes documented at the latest "
                f"visit ({latest.date}): "
                + " ".join(notes)
                + "."
            )

    # ======================================================
    # MEDICAL HISTORY
    # ======================================================

    elif (
        "history" in q
        or "medical history" in q
        or "past medical history" in q
    ):

        history = patient.medical_history

        if history:

            answer = (
                "Medical history: "
                + ", ".join(history)
                + "."
            )

            for item in history:

                evidence.append({
                    "visit_date": "patient history",
                    "source_type": "medical_history",
                    "content": item
                })

        else:

            answer = (
                "No medical history is documented."
            )

    # ======================================================
    # WHAT CHANGED BETWEEN VISITS?
    # ======================================================

    elif (
        "what changed" in q
        or "changes between" in q
        or "change between" in q
        or "changes" in q
        or "compare visits" in q
        or "compared with" in q
    ):

        if len(visits) < 2:

            answer = (
                "At least two visits are required "
                "to compare changes."
            )

        else:

            comparison = compare_visits(patient)

            if not comparison["changes"]:

                answer = (
                    f"No documented changes were found "
                    f"between {comparison['previous_visit']} "
                    f"and {comparison['latest_visit']}."
                )

            else:

                answer = (
                    f"Documented changes between "
                    f"{comparison['previous_visit']} and "
                    f"{comparison['latest_visit']}: "
                    + " ".join(comparison["summary"])
                )

                # Add evidence for each change
                for change in comparison["changes"]:

                    evidence.append({
                        "visit_date": comparison["latest_visit"],
                        "source_type": change["type"],
                        "content": str(change)
                    })

    # ======================================================
    # HbA1c QUESTIONS
    # ======================================================

    elif "hba1c" in q:

        results = []

        for visit in visits:

            for lab in visit.lab_results:

                if lab.name.lower() == "hba1c":

                    results.append(
                        (
                            visit.date,
                            lab.value,
                            lab.unit
                        )
                    )

                    evidence.append({
                        "visit_date": visit.date,
                        "source_type": "lab_result",
                        "content": (
                            f"HbA1c: "
                            f"{lab.value} "
                            f"{lab.unit}"
                        )
                    })

        if not results:

            answer = "No HbA1c results are documented."

        elif len(results) == 1:

            date, value, unit = results[0]

            answer = (
                f"HbA1c was "
                f"{value} {unit} "
                f"on {date}."
            )

        else:

            first = results[0]
            last = results[-1]

            difference = last[1] - first[1]

            answer = (
                f"HbA1c was "
                f"{first[1]} {first[2]} "
                f"on {first[0]} and "
                f"{last[1]} {last[2]} "
                f"on {last[0]}. "
                f"The recorded difference is "
                f"{difference:+.2f} {last[2]}."
            )

    # ======================================================
    # SPECIFIC LAB RESULT QUESTIONS
    # ======================================================

    else:

        # Try to identify a laboratory name from the question
        matching_lab = None

        for visit in visits:

            for lab in visit.lab_results:

                lab_name = lab.name.lower()

                if lab_name in q:

                    matching_lab = lab.name
                    break

            if matching_lab:
                break

        if matching_lab:

            results = []

            for visit in visits:

                for lab in visit.lab_results:

                    if (
                        lab.name.lower()
                        == matching_lab.lower()
                    ):

                        results.append(
                            (
                                visit.date,
                                lab.value,
                                lab.unit
                            )
                        )

                        evidence.append({
                            "visit_date": visit.date,
                            "source_type": "lab_result",
                            "content": (
                                f"{lab.name}: "
                                f"{lab.value} "
                                f"{lab.unit}"
                            )
                        })

            if len(results) == 1:

                date, value, unit = results[0]

                answer = (
                    f"{matching_lab} was "
                    f"{value} {unit} "
                    f"on {date}."
                )

            else:

                first = results[0]
                last = results[-1]

                difference = last[1] - first[1]

                answer = (
                    f"{matching_lab} was "
                    f"{first[1]} {first[2]} "
                    f"on {first[0]} and "
                    f"{last[1]} {last[2]} "
                    f"on {last[0]}. "
                    f"The recorded difference is "
                    f"{difference:+.2f} {last[2]}."
                )

        else:

            # ==================================================
            # UNSUPPORTED QUESTION
            # ==================================================

            answer = (
                "I can currently answer questions about "
                "medications, laboratory results, clinical "
                "notes, medical history, HbA1c, specific "
                "laboratory values, and documented changes "
                "between visits."
            )

    # ======================================================
    # FINAL RESPONSE
    # ======================================================

    return {
        "question": question,
        "answer": answer,
        "evidence": evidence
    }