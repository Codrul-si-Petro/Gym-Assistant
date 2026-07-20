// Plan Workout page — stamp one set template onto multiple calendar dates.

if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "::1"
) {
    API_BASE = "http://127.0.0.1:8000";
} else {
    API_BASE = "https://api.gym-assistant.app";
}

var exerciseMap = {};
var attachmentMap = {};
var equipmentMap = {};
var PLACEHOLDER_DIMENSION_ID = -1;
var planDates = [];

function getAuthHeaders() {
    var token = localStorage.getItem("access_token");
    if (!token) return null;
    return {
        Authorization: "Bearer " + token,
        Accept: "application/json",
        "Content-Type": "application/json",
    };
}

function showMessage(text, type) {
    var el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = "message " + (type === "success" ? "success" : "error");
    el.removeAttribute("hidden");
}

function clearMessage() {
    var el = document.getElementById("message");
    if (!el) return;
    el.setAttribute("hidden", "hidden");
    el.textContent = "";
}

function fillDimensionList(listId, items, nameKey, idKey, mapRef) {
    var list = document.getElementById(listId);
    if (!list) return;
    list.replaceChildren();
    (items || []).forEach(function (item) {
        var opt = document.createElement("option");
        opt.value = item[nameKey];
        list.appendChild(opt);
        mapRef[item[nameKey]] = item[idKey];
    });
}

function loadOptions() {
    var headers = getAuthHeaders();
    if (!headers) {
        showMessage("Please log in to plan workouts.", "error");
        return;
    }
    Promise.all([
        fetch(API_BASE + "/api/exercises/", { headers: headers }).then(function (r) {
            return r.ok ? r.json() : [];
        }),
        fetch(API_BASE + "/api/attachments/", { headers: headers }).then(function (r) {
            return r.ok ? r.json() : [];
        }),
        fetch(API_BASE + "/api/equipment/", { headers: headers }).then(function (r) {
            return r.ok ? r.json() : [];
        }),
    ])
        .then(function (results) {
            fillDimensionList("exercises_list", results[0], "exercise_name", "exercise_id", exerciseMap);
            fillDimensionList("attachments_list", results[1], "attachment_name", "attachment_id", attachmentMap);
            fillDimensionList("equipment_list", results[2], "equipment_name", "equipment_id", equipmentMap);
        })
        .catch(function () {
            showMessage("Could not load exercise lists.", "error");
        });
}

function dimensionIdFromName(map, name) {
    if (map[name] != null) return map[name];
    if (name === "None") return PLACEHOLDER_DIMENSION_ID;
    return null;
}

function renderPlanDatesList() {
    var list = document.getElementById("plan_dates_list");
    if (!list) return;
    list.replaceChildren();
    planDates.slice().sort().forEach(function (d) {
        var li = document.createElement("li");
        li.textContent = d;
        var removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.setAttribute("aria-label", "Remove " + d);
        removeBtn.textContent = "×";
        removeBtn.addEventListener("click", function () {
            planDates = planDates.filter(function (x) {
                return x !== d;
            });
            renderPlanDatesList();
        });
        li.appendChild(removeBtn);
        list.appendChild(li);
    });
}

function getPayload() {
    if (!planDates.length) {
        showMessage("Add at least one plan date.", "error");
        return null;
    }
    var exerciseName = (document.getElementById("exercise_name").value || "").trim();
    if (!exerciseMap[exerciseName]) {
        showMessage("Pick a valid exercise from the list.", "error");
        return null;
    }
    var attachmentName = (document.getElementById("attachment_name").value || "").trim() || "None";
    var equipmentName = (document.getElementById("equipment_name").value || "").trim() || "None";
    return {
        dates: planDates.slice().sort(),
        exercise: exerciseMap[exerciseName],
        attachment: dimensionIdFromName(attachmentMap, attachmentName),
        equipment: dimensionIdFromName(equipmentMap, equipmentName),
        repetitions: parseInt(document.getElementById("repetitions").value, 10) || 1,
        load: parseFloat(document.getElementById("load").value) || 0,
        unit: document.getElementById("unit").value || "KG",
        set_type: (document.getElementById("set_type").value || "").trim() || "Working set",
        comments: (document.getElementById("comments").value || "").trim() || "None",
        workout_split: (document.getElementById("workout_split").value || "").trim() || "None",
    };
}

function onSubmit(e) {
    e.preventDefault();
    clearMessage();
    var headers = getAuthHeaders();
    if (!headers) {
        showMessage("Please log in first.", "error");
        return;
    }
    var payload = getPayload();
    if (!payload) return;

    var btn = document.getElementById("submit-btn");
    btn.disabled = true;
    fetch(API_BASE + "/api/workouts/plan-batch/", {
        method: "POST",
        headers: headers,
        body: JSON.stringify(payload),
    })
        .then(function (res) {
            return res.json().then(function (data) {
                return { status: res.status, data: data };
            });
        })
        .then(function (result) {
            if (result.status >= 200 && result.status < 300) {
                var count = result.data && result.data.count != null ? result.data.count : planDates.length;
                showMessage("Plan saved on " + count + " date" + (count === 1 ? "" : "s") + ".", "success");
                document.getElementById("repetitions").value = "8";
                document.getElementById("load").value = "0";
                document.getElementById("comments").value = "";
            } else {
                var detail = result.data && (result.data.detail || JSON.stringify(result.data));
                showMessage(detail || "Could not save plan.", "error");
            }
        })
        .catch(function () {
            showMessage("Network error. Try again.", "error");
        })
        .finally(function () {
            btn.disabled = false;
        });
}

document.addEventListener("DOMContentLoaded", function () {
    loadOptions();
    renderPlanDatesList();
    document.getElementById("plan_date_add").addEventListener("click", function () {
        var picker = document.getElementById("plan_date_picker");
        var val = picker && picker.value;
        if (!val) {
            showMessage("Pick a date to add.", "error");
            return;
        }
        if (planDates.indexOf(val) === -1) {
            planDates.push(val);
            renderPlanDatesList();
        }
        picker.value = "";
        clearMessage();
    });
    document.getElementById("workout-plan-form").addEventListener("submit", onSubmit);
});
