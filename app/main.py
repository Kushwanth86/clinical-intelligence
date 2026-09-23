from fastapi import FastAPI

from app.models import PatientRecord, ComparisonReport
from app.ai import compare_visits


app = FastAPI(
    title="Clinical Intelligence Copilot",
    description="A clinical decision-support prototype using synthetic patient data.",
    version="0.1.0"
)


@app.get("/")
def home():
    return {
        "message": "Clinical Intelligence Copilot is running"
    }


@app.post(
    "/compare",
    response_model=ComparisonReport
)
def compare(patient: PatientRecord):

    result = compare_visits(patient)

    return result