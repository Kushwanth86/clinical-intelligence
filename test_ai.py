from app.ai import analyze_record


record = """
Patient is 52 years old.
History: hypertension and type 2 diabetes.
HbA1c increased from 7.2% to 8.1%.
Patient reports increased fatigue.
"""


result = analyze_record(record)

print("\n--- AI ANALYSIS ---\n")
print(result)