from typing import Any, List, Optional

from pydantic import BaseModel


class LabResult(BaseModel):
    name: str
    value: float
    unit: str


class Medication(BaseModel):
    name: str
    dosage: str


class Visit(BaseModel):
    date: str
    medications: List[Medication]
    lab_results: List[LabResult]
    clinical_notes: List[str]


class PatientRecord(BaseModel):
    patient_id: str
    age: int
    medical_history: List[str]
    visits: List[Visit]


class Change(BaseModel):
    type: str
    name: Optional[str] = None
    previous: Optional[Any] = None
    current: Optional[Any] = None
    difference: Optional[float] = None
    unit: Optional[str] = None


class ComparisonReport(BaseModel):
    patient_id: str
    previous_visit: str
    latest_visit: str
    changes: List[Change]
    summary: List[str]


class AskRequest(BaseModel):
    patient: PatientRecord
    question: str


class Evidence(BaseModel):
    visit_date: str
    source_type: str
    content: str


class AskResponse(BaseModel):
    question: str
    answer: str
    evidence: List[Evidence]