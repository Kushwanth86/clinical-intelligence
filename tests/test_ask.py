from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


PATIENT = {
    "patient_id": "P001",
    "age": 52,
    "medical_history": [
        "Hypertension",
        "Type 2 diabetes",
    ],
    "visits": [
        {
            "date": "2026-01-10",
            "medications": [
                {
                    "name": "Metformin",
                    "dosage": "500 mg twice daily",
                },
                {
                    "name": "Lisinopril",
                    "dosage": "10 mg once daily",
                },
            ],
            "lab_results": [
                {
                    "name": "HbA1c",
                    "value": 7.2,
                    "unit": "%",
                },
                {
                    "name": "Creatinine",
                    "value": 0.9,
                    "unit": "mg/dL",
                },
            ],
            "clinical_notes": [
                "Patient reports occasional fatigue.",
            ],
        },
        {
            "date": "2026-06-15",
            "medications": [
                {
                    "name": "Metformin",
                    "dosage": "500 mg twice daily",
                },
                {
                    "name": "Lisinopril",
                    "dosage": "20 mg once daily",
                },
                {
                    "name": "Atorvastatin",
                    "dosage": "20 mg once daily",
                },
            ],
            "lab_results": [
                {
                    "name": "HbA1c",
                    "value": 8.1,
                    "unit": "%",
                },
                {
                    "name": "Creatinine",
                    "value": 1.1,
                    "unit": "mg/dL",
                },
                {
                    "name": "LDL Cholesterol",
                    "value": 145,
                    "unit": "mg/dL",
                },
            ],
            "clinical_notes": [
                "Patient reports increased fatigue over the past month.",
            ],
        },
    ],
}


def ask(question):
    return client.post(
        "/ask",
        json={
            "patient": PATIENT,
            "question": question,
        },
    )


def test_ask_medications_returns_latest_medications_and_evidence():
    response = ask("What medications is the patient taking?")

    assert response.status_code == 200

    data = response.json()

    assert "Metformin (500 mg twice daily)" in data["answer"]
    assert "Lisinopril (20 mg once daily)" in data["answer"]
    assert "Atorvastatin (20 mg once daily)" in data["answer"]

    assert len(data["evidence"]) == 3
    assert all(
        item["source_type"] == "medication"
        for item in data["evidence"]
    )


def test_ask_latest_labs_returns_latest_results_and_evidence():
    response = ask("What are the latest lab results?")

    assert response.status_code == 200

    data = response.json()

    assert "HbA1c (8.1 %)" in data["answer"]
    assert "Creatinine (1.1 mg/dL)" in data["answer"]
    assert "LDL Cholesterol (145 mg/dL)" in data["answer"]

    assert len(data["evidence"]) == 3
    assert all(
        item["visit_date"] == "2026-06-15"
        for item in data["evidence"]
    )


def test_ask_clinical_notes_returns_latest_notes():
    response = ask("What clinical notes are documented?")

    assert response.status_code == 200

    data = response.json()

    assert (
        "Patient reports increased fatigue over the past month."
        in data["answer"]
    )

    assert data["evidence"] == [
        {
            "visit_date": "2026-06-15",
            "source_type": "clinical_note",
            "content": (
                "Patient reports increased fatigue over the past month."
            ),
        }
    ]


def test_ask_medical_history_returns_history_and_evidence():
    response = ask("What is the patient's medical history?")

    assert response.status_code == 200

    data = response.json()

    assert "Hypertension" in data["answer"]
    assert "Type 2 diabetes" in data["answer"]

    assert len(data["evidence"]) == 2
    assert all(
        item["source_type"] == "medical_history"
        for item in data["evidence"]
    )


def test_ask_changes_returns_documented_changes_and_evidence():
    response = ask("What changed between visits?")

    assert response.status_code == 200

    data = response.json()

    assert "HbA1c increased" in data["answer"]
    assert "Lisinopril dosage changed" in data["answer"]
    assert "Atorvastatin" in data["answer"]

    assert len(data["evidence"]) == 6


def test_ask_hba1c_returns_longitudinal_values():
    response = ask("How has the HbA1c changed?")

    assert response.status_code == 200

    data = response.json()

    assert "7.2 %" in data["answer"]
    assert "2026-01-10" in data["answer"]
    assert "8.1 %" in data["answer"]
    assert "2026-06-15" in data["answer"]
    assert "+0.90 %" in data["answer"]

    assert len(data["evidence"]) == 2


def test_ask_specific_lab_returns_longitudinal_values():
    response = ask("What happened to creatinine?")

    assert response.status_code == 200

    data = response.json()

    assert "0.9 mg/dL" in data["answer"]
    assert "1.1 mg/dL" in data["answer"]
    assert "+0.20 mg/dL" in data["answer"]

    assert len(data["evidence"]) == 2


def test_ask_without_visits_returns_empty_evidence():
    patient = {
        **PATIENT,
        "visits": [],
    }

    response = client.post(
        "/ask",
        json={
            "patient": patient,
            "question": "What medications is the patient taking?",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "No visits are available for this patient."
    assert data["evidence"] == []


def test_ask_unsupported_question_returns_supported_topics():
    response = ask("What should the treatment plan be?")

    assert response.status_code == 200

    data = response.json()

    assert "medications" in data["answer"]
    assert "laboratory values" in data["answer"]
    assert data["evidence"] == []
