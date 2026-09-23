const patient = {
  patient_id: "P001",
  age: 52,

  medical_history: [
    "Hypertension",
    "Type 2 diabetes"
  ],

  visits: [
    {
      date: "2026-01-10",

      medications: [
        {
          name: "Metformin",
          dosage: "500 mg twice daily"
        },
        {
          name: "Lisinopril",
          dosage: "10 mg once daily"
        }
      ],

      lab_results: [
        {
          name: "HbA1c",
          value: 7.2,
          unit: "%"
        },
        {
          name: "Creatinine",
          value: 0.9,
          unit: "mg/dL"
        }
      ],

      clinical_notes: [
        "Patient reports occasional fatigue."
      ]
    },

    {
      date: "2026-06-15",

      medications: [
        {
          name: "Metformin",
          dosage: "500 mg twice daily"
        },
        {
          name: "Lisinopril",
          dosage: "20 mg once daily"
        },
        {
          name: "Atorvastatin",
          dosage: "20 mg once daily"
        }
      ],

      lab_results: [
        {
          name: "HbA1c",
          value: 8.1,
          unit: "%"
        },
        {
          name: "Creatinine",
          value: 1.1,
          unit: "mg/dL"
        },
        {
          name: "LDL Cholesterol",
          value: 145,
          unit: "mg/dL"
        }
      ],

      clinical_notes: [
        "Patient reports increased fatigue over the past month."
      ]
    }
  ]
};


// --------------------------------------------------
// HELPER
// --------------------------------------------------

const $ = (id) => document.getElementById(id);


// --------------------------------------------------
// ASK THE COPILOT
// --------------------------------------------------

$("askButton").addEventListener("click", async () => {

  const button = $("askButton");
  const question = $("question").value.trim();

  if (!question) {
    return;
  }

  button.disabled = true;
  button.textContent = "Thinking...";

  $("answer").textContent =
    "Analyzing the structured patient record...";

  $("evidence").innerHTML = "";

  try {

    const response = await fetch("/ask", {
      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        patient: patient,
        question: question
      })
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    const data = await response.json();

    // Show answer
    $("answer").textContent = data.answer;


    // Show evidence
    if (data.evidence && data.evidence.length > 0) {

     $("evidence").innerHTML = data.evidence
  .map((item) => {

    let content = item.content;

    // Make longitudinal change evidence readable
    if (item.source_type === "lab_change") {

      const match = content.match(
        /'name': '([^']+)', 'previous': ([^,]+), 'current': ([^,]+).*?'unit': '([^']+)'/
      );

      if (match) {
        content =
          `${match[1]} changed from ${match[2]} ${match[4]} to ${match[3]} ${match[4]}.`;
      }
    }

    else if (item.source_type === "new_lab_result") {

      const match = content.match(
        /'name': '([^']+)',.*?'current': ([^,]+).*?'unit': '([^']+)'/
      );

      if (match) {
        content =
          `${match[1]} was newly documented at ${match[2]} ${match[3]}.`;
      }
    }

    else if (item.source_type === "medication_change") {

      const match = content.match(
        /'name': '([^']+)', 'previous': '([^']+)', 'current': '([^']+)'/
      );

      if (match) {
        content =
          `${match[1]} changed from ${match[2]} to ${match[3]}.`;
      }
    }

    else if (item.source_type === "new_medication") {

      const match = content.match(
        /'name': '([^']+)',.*?'current': '([^']+)'/
      );

      if (match) {
        content =
          `${match[1]} was newly documented at ${match[2]}.`;
      }
    }

    else if (item.source_type === "clinical_note_change") {

      const match = content.match(
        /'previous': '([^']+)', 'current': '([^']+)'/
      );

      if (match) {
        content =
          `Previous: ${match[1]} Current: ${match[2]}`;
      }
    }

    return `
      <div class="evidence-item">

        <strong>
          ${item.source_type.replaceAll("_", " ")} · ${item.visit_date}
        </strong>

        <span>
          ${content}
        </span>

      </div>
    `;

  })
  .join("");

    } else {

      $("evidence").innerHTML =
        '<div class="empty">No supporting evidence found.</div>';

    }

  } catch (error) {

    console.error(error);

    $("answer").textContent =
      "Request failed. Check the FastAPI terminal for details.";

    $("evidence").innerHTML =
      '<div class="empty">No evidence available.</div>';

  } finally {

    button.disabled = false;
    button.textContent = "Ask";

  }

});


// --------------------------------------------------
// COMPARE VISITS
// --------------------------------------------------

$("compareButton").addEventListener("click", async () => {

  const button = $("compareButton");

  button.disabled = true;
  button.textContent = "Comparing...";

  $("changes").innerHTML =
    '<div class="empty">Comparing patient visits...</div>';

  try {

    const response = await fetch("/compare", {
      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify(patient)
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    const data = await response.json();


    // --------------------------------------------------
    // NO CHANGES
    // --------------------------------------------------

    if (!data.changes || data.changes.length === 0) {

      $("changes").innerHTML =
        '<div class="empty">No changes detected between the two latest visits.</div>';

      return;
    }


    // --------------------------------------------------
    // RENDER CHANGES
    // --------------------------------------------------

    $("changes").innerHTML = data.changes
      .map((change) => {

        let text = "";


        // ----------------------------------------------
        // LABORATORY VALUE CHANGED
        // ----------------------------------------------

        if (change.type === "lab_change") {

          text =
            `${change.name}: ` +
            `${change.previous} ${change.unit} → ` +
            `${change.current} ${change.unit}`;

        }


        // ----------------------------------------------
        // NEW LAB RESULT
        // ----------------------------------------------

        else if (change.type === "new_lab_result") {

          text =
            `${change.name} added: ` +
            `${change.current} ${change.unit}`;

        }


        // ----------------------------------------------
        // MEDICATION DOSAGE CHANGED
        // ----------------------------------------------

        else if (change.type === "medication_change") {

          text =
            `${change.name}: ` +
            `${change.previous} → ` +
            `${change.current}`;

        }


        // ----------------------------------------------
        // NEW MEDICATION
        // ----------------------------------------------

        else if (change.type === "new_medication") {

          text =
            `${change.name} added: ` +
            `${change.current}`;

        }


        // ----------------------------------------------
        // CLINICAL NOTE CHANGED
        // ----------------------------------------------

        else if (change.type === "clinical_note_change") {

          text =
            `Previous note: ${change.previous}<br>` +
            `Current note: ${change.current}`;

        }


        // ----------------------------------------------
        // NEW CLINICAL NOTE
        // ----------------------------------------------

        else if (change.type === "new_clinical_note") {

          text =
            `New clinical note: ${change.current}`;

        }


        // ----------------------------------------------
        // FALLBACK
        // ----------------------------------------------

        else {

          text =
            "Change detected: " +
            JSON.stringify(change);

        }


        // ----------------------------------------------
        // DISPLAY TYPE
        // ----------------------------------------------

        const displayType = change.type
          ? change.type
              .replaceAll("_", " ")
              .toUpperCase()
          : "CHANGE";


        // ----------------------------------------------
        // HTML CARD
        // ----------------------------------------------

        return `
          <div class="change">

            <div class="change-type">
              ${displayType}
            </div>

            <div class="change-text">
              ${text}
            </div>

          </div>
        `;

      })
      .join("");

  } catch (error) {

    console.error(error);

    $("changes").innerHTML =
      '<div class="empty">Comparison failed. Check the FastAPI terminal.</div>';

  } finally {

    button.disabled = false;
    button.textContent = "Compare visits";

  }

});
// --------------------------------------------------
// PATIENT TIMELINE
// --------------------------------------------------

function renderTimeline() {

  const timeline = $("timeline");

  if (!timeline) {
    return;
  }

  timeline.innerHTML = "";

  patient.visits
    .slice()
    .sort((a, b) => a.date.localeCompare(b.date))
    .forEach((visit, index) => {

      const medications = visit.medications
        .map((medication) =>
          `${medication.name} ${medication.dosage}`
        )
        .join(" · ");

      const labs = visit.lab_results
        .map((lab) =>
          `${lab.name} ${lab.value} ${lab.unit}`
        )
        .join(" · ");

      const notes = visit.clinical_notes
        .map((note) => note)
        .join(" ");

      const isLatest =
        index === patient.visits.length - 1;

      timeline.innerHTML += `
        <div class="timeline-item">

          <div class="timeline-date">
            ${visit.date}
          </div>

          <div class="timeline-content">

            <strong>
              ${isLatest ? "Latest documented visit" : "Documented visit"}
            </strong>

            <p>
              <strong>Medications:</strong>
              ${medications || "None documented"}
            </p>

            <p>
              <strong>Laboratory results:</strong>
              ${labs || "None documented"}
            </p>

            <p>
              <strong>Clinical notes:</strong>
              ${notes || "None documented"}
            </p>

          </div>

        </div>
      `;
    });
}


// Render timeline when page loads
renderTimeline();
// --------------------------------------------------
// PATIENT HEADER
// --------------------------------------------------

function renderPatientHeader() {

  $("patientName").textContent = patient.patient_id;

  $("patientMeta").textContent =
    `${patient.age} years · ${patient.medical_history.join(" · ")}`;

  const latestVisit = patient.visits
    .slice()
    .sort((a, b) => a.date.localeCompare(b.date))
    .at(-1);

  if (latestVisit) {
    $("latestDate").textContent = latestVisit.date;
  }
}


// Render patient header when page loads
renderPatientHeader();