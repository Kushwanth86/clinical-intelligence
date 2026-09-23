const patient = {
  patient_id: "P001",
  age: 52,
  medical_history: ["Hypertension", "Type 2 diabetes"],
  visits: [
    {
      date: "2026-01-10",
      medications: [
        { name: "Metformin", dosage: "500 mg twice daily" },
        { name: "Lisinopril", dosage: "10 mg once daily" }
      ],
      lab_results: [
        { name: "HbA1c", value: 7.2, unit: "%" },
        { name: "Creatinine", value: 0.9, unit: "mg/dL" }
      ],
      clinical_notes: ["Patient reports occasional fatigue."]
    },
    {
      date: "2026-06-15",
      medications: [
        { name: "Metformin", dosage: "500 mg twice daily" },
        { name: "Lisinopril", dosage: "20 mg once daily" },
        { name: "Atorvastatin", dosage: "20 mg once daily" }
      ],
      lab_results: [
        { name: "HbA1c", value: 8.1, unit: "%" },
        { name: "Creatinine", value: 1.1, unit: "mg/dL" },
        { name: "LDL Cholesterol", value: 145, unit: "mg/dL" }
      ],
      clinical_notes: ["Patient reports increased fatigue over the past month."]
    }
  ]
};

const $ = (id) => document.getElementById(id);

$("askButton").addEventListener("click", async () => {
  const button = $("askButton");
  const question = $("question").value.trim();

  if (!question) return;

  button.disabled = true;
  button.textContent = "Thinking...";
  $("answer").className = "answer";
  $("answer").textContent = "Analyzing the structured patient record...";
  $("evidence").innerHTML = "";

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patient, question })
    });

    if (!response.ok) throw new Error(await response.text());

    const data = await response.json();
    $("answer").textContent = data.answer;

    $("evidence").innerHTML = data.evidence.map(item => `
      <div class="evidence-item">
        <strong>${item.source_type} · ${item.visit_date}</strong>
        <span>${item.content}</span>
      </div>
    `).join("");
  } catch (error) {
    $("answer").textContent = "Request failed. Check the FastAPI terminal for details.";
    console.error(error);
  } finally {
    button.disabled = false;
    button.textContent = "Ask";
  }
});

$("compareButton").addEventListener("click", async () => {
  const button = $("compareButton");
  button.disabled = true;
  button.textContent = "Comparing...";

  try {
    const response = await fetch("/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patient)
    });

    if (!response.ok) throw new Error(await response.text());

    const data = await response.json();

    $("changes").innerHTML = data.summary.length
      ? data.summary.map((text, index) => `
          <div class="change">
            <div class="change-type">${data.changes[index]?.type || "change"}</div>
            <div class="change-text">${text}</div>
          </div>
        `).join("")
      : '<div class="empty">No changes detected between the two latest visits.</div>';
  } catch (error) {
    $("changes").innerHTML = '<div class="empty">Comparison failed. Check the FastAPI terminal.</div>';
    console.error(error);
  } finally {
    button.disabled = false;
    button.textContent = "Compare visits";
  }
});
