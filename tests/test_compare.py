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


def test_compare_detects_all_expected_changes():
    response = client.post("/compare", json=PATIENT)

    assert response.status_code == 200

    data = response.json()

    assert data["patient_id"] == "P001"
    assert data["previous_visit"] == "2026-01-10"
    assert data["latest_visit"] == "2026-06-15"

    change_types = [
        change["type"]
        for change in data["changes"]
    ]

    assert change_types == [
        "lab_change",
        "lab_change",
        "new_lab_result",
        "medication_change",
        "new_medication",
        "clinical_note_change",
    ]

    assert data["changes"][0]["name"] == "HbA1c"
    assert data["changes"][0]["previous"] == 7.2
    assert data["changes"][0]["current"] == 8.1
    assert data["changes"][0]["difference"] == 0.9

    assert data["changes"][1]["name"] == "Creatinine"
    assert data["changes"][1]["previous"] == 0.9
    assert data["changes"][1]["current"] == 1.1
    assert data["changes"][1]["difference"] == 0.2

    assert data["changes"][2]["name"] == "LDL Cholesterol"
    assert data["changes"][2]["current"] == 145

    assert data["changes"][3]["name"] == "Lisinopril"
    assert data["changes"][3]["previous"] == "10 mg once daily"
    assert data["changes"][3]["current"] == "20 mg once daily"

    assert data["changes"][4]["name"] == "Atorvastatin"
    assert data["changes"][4]["current"] == "20 mg once daily"

    assert (
        data["changes"][5]["previous"]
        == "patient reports occasional fatigue."
    )

    assert (
        data["changes"][5]["current"]
        == "Patient reports increased fatigue over the past month."
    )

    assert len(data["summary"]) == 6


def test_compare_requires_two_visits():
    patient = {
        **PATIENT,
        "visits": [PATIENT["visits"][0]],
    }

    response = client.post("/compare", json=patient)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "At least two visits are required for comparison."
    )
