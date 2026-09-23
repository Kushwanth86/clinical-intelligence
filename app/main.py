from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import PatientRecord, ComparisonReport, AskRequest, AskResponse
from app.ai import compare_visits, answer_question


app = FastAPI(
    title="Clinical Intelligence Copilot",
    description="A clinical decision-support prototype using synthetic patient data.",
    version="0.2.0"
)

app.mount("/static", StaticFiles(directory="web"), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse("web/index.html")


@app.post("/compare", response_model=ComparisonReport)
def compare(patient: PatientRecord):
    try:
        return compare_visits(patient)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    return answer_question(request.patient, request.question)
