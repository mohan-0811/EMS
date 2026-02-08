const form = document.getElementById("incident-form");
const resultPanel = document.getElementById("dispatch-result");
const resourceList = document.getElementById("resource-list");

async function loadResources() {
  const response = await fetch("/api/resources");
  const resources = await response.json();
  resourceList.innerHTML = resources
    .map(
      (resource) => `
        <div class="resource-card">
          <strong>${resource.name}</strong>
          <p>Type: ${resource.resource_type}</p>
          <p>Status: ${resource.status}</p>
          <p>Ready in ${resource.readiness_minutes} min · Avg speed ${resource.avg_speed_kmph} km/h</p>
        </div>
      `
    )
    .join("");
}

function renderDispatch(payload) {
  const selected = payload.selected_resource || {};
  const dispatch = payload.dispatch || {};
  resultPanel.innerHTML = `
    <h3>Dispatch Summary</h3>
    <p><strong>Incident ID:</strong> ${payload.incident_id ?? "-"}</p>
    <p><strong>Priority Score:</strong> ${payload.priority_score ?? "-"}</p>
    <p><strong>Assigned Resource:</strong> ${selected.resource_name ?? "-"}</p>
    <p><strong>Resource Type:</strong> ${selected.resource_type ?? "-"}</p>
    <p><strong>Estimated ETA:</strong> ${dispatch.eta_minutes ?? "-"} minutes</p>
    <p><strong>Status:</strong> ${dispatch.dispatch_status ?? "Pending"}</p>
  `;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  payload.victim_count = Number(payload.victim_count);
  payload.time_sensitivity = Number(payload.time_sensitivity);
  payload.latitude = Number(payload.latitude);
  payload.longitude = Number(payload.longitude);

  const response = await fetch("/api/incidents", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    resultPanel.innerHTML = `<p>Error: ${data.error || "Unable to dispatch"}</p>`;
    return;
  }
  renderDispatch(data);
});

loadResources();
