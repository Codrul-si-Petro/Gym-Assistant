// Use localhost/127 if running locally, otherwise use current host
if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
  API_BASE = "http://127.0.0.1:8000"; // local backend
} else {
  API_BASE = 'https://api.gym-assistant.app';
}

function getAuthHeaders() {
    const token = localStorage.getItem("access_token");
    if (!token) return null;
    return {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/json",
        "Content-Type": "application/json",
    };
}

async function fetchWorkouts() {
    const headers = getAuthHeaders();
    if (!headers) {
        document.getElementById("auth-msg").textContent = "Not logged in. Log in to see workouts.";
        document.getElementById("workout-tbody").innerHTML =
            '<tr><td colspan="13" class="empty-msg">Not logged in</td></tr>';
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/api/workouts/`, { headers });
        if (res.status === 401) {
            document.getElementById("auth-msg").textContent = "Session expired. Please log in again.";
            document.getElementById("workout-tbody").innerHTML =
                '<tr><td colspan="13" class="empty-msg">Unauthorized</td></tr>';
            return;
        }
        const data = await res.json();
        const tbody = document.getElementById("workout-tbody");
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="13" class="empty-msg">No workouts found</td></tr>';
            return;
        }
        const exerciseMap = {};
        const attachmentMap = {};
        const equipmentMap = {};
        try {
            const [exRes, atRes, eqRes] = await Promise.all([
                fetch(`${API_BASE}/api/exercises/`, { headers }),
                fetch(`${API_BASE}/api/attachments/`, { headers }),
                fetch(`${API_BASE}/api/equipment/`, { headers }),
            ]);
            const [exJson, atJson, eqJson] = await Promise.all([exRes.json(), atRes.json(), eqRes.json()]);
            (exJson || []).forEach(e => { exerciseMap[e.exercise_id] = e.exercise_name; });
            (atJson || []).forEach(a => { attachmentMap[a.attachment_id] = a.attachment_name; });
            (eqJson || []).forEach(e => { equipmentMap[e.equipment_id] = e.equipment_name; });
        } catch (_) { /* use IDs if lookups fail */ }

          tbody.innerHTML = data.map(row => {
              const date = row.ta_created_at ? row.ta_created_at.slice(0, 10) : "";
              const exercise = exerciseMap[row.exercise] ?? row.exercise;
              const attachment = attachmentMap[row.attachment] ?? row.attachment;
              const equipment = equipmentMap[row.equipment] ?? row.equipment;
              return `<tr>
                  <td>${row.workout_number}</td>
                  <td>${date}</td>
                  <td>${escapeHtml(String(exercise))}</td>
                  <td>${row.set_number}</td>
                  <td>${row.repetitions}</td>
                  <td>${row.load}</td>
                  <td>${escapeHtml(String(equipment))}</td>
                  <td>${escapeHtml(String(attachment))}</td>
                  <td>${row.unit}</td>
                  <td>${escapeHtml(String(row.set_type || ""))}</td>
                  <td>${escapeHtml(String(row.comments || ""))}</td>
                  <td>${escapeHtml(String(row.workout_split || ""))}</td>
              </tr>`;
          }).join("");

    } catch (err) {
        document.getElementById("auth-msg").textContent = "Failed to load workouts.";
        document.getElementById("workout-tbody").innerHTML =
            '<tr><td colspan="13" class="empty-msg">Error loading data</td></tr>';
    }
}

function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
}

fetchWorkouts();
