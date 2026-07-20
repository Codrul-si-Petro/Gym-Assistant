// Plan Workout page — stamp one set template onto multiple calendar dates.

var exerciseMap = {};
var attachmentMap = {};
var equipmentMap = {};
var planDates = [];

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

function loadOptions() {
    loadDimensionOptions(
        { exerciseMap: exerciseMap, attachmentMap: attachmentMap, equipmentMap: equipmentMap },
        {
            loginMessage: "Please log in to plan workouts.",
            loadErrorMessage: "Could not load exercise lists.",
        }
    );
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
