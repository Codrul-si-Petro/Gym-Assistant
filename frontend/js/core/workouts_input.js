// Use localhost/127 if running locally, otherwise use current host
if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    API_BASE = "http://127.0.0.1:8000";
} else {
    API_BASE = "https://api.gym-assistant.app";
}

var exerciseMap = {};
var attachmentMap = {};
var equipmentMap = {};

/** Default time before success messages fade (ms). */
var DEFAULT_SUCCESS_MS = 3500;
/** Delete-last confirmation: keep visible longer (5–10s range). */
var DELETE_SUCCESS_MS = 7500;
var MESSAGE_FADE_MS = 300;
var MESSAGE_MIN_MS = 1000;

/** Cleared when a new success message is shown so old timers do not clear the new text. */
var successHideTimer = null;
var successFadeTimer = null;

function getAuthHeaders() {
    var token = localStorage.getItem("access_token");
    if (!token) return null;
    return {
        Authorization: "Bearer " + token,
        Accept: "application/json",
        "Content-Type": "application/json",
    };
}

function cancelSuccessTimers() {
    if (successHideTimer !== null) {
        clearTimeout(successHideTimer);
        successHideTimer = null;
    }
    if (successFadeTimer !== null) {
        clearTimeout(successFadeTimer);
        successFadeTimer = null;
    }
}

/**
 * @param {string} text
 * @param {"success"|"error"} type
 * @param {number} [duration] visible time before fade (success only); defaults to DEFAULT_SUCCESS_MS
 */
function showMessage(text, type, duration) {
    var el = document.getElementById("message");
    if (!el) return;

    cancelSuccessTimers();

    el.textContent = text;
    el.className = "message " + (type === "success" ? "success" : "error");
    el.removeAttribute("hidden");
    el.style.opacity = "";
    el.style.transition = "";

    if (type !== "success") {
        return;
    }

    var effectiveDuration = Math.max(
        duration != null ? duration : DEFAULT_SUCCESS_MS,
        MESSAGE_MIN_MS
    );

    successHideTimer = setTimeout(function () {
        successHideTimer = null;
        el.style.opacity = "0";
        el.style.transition = "opacity " + MESSAGE_FADE_MS + "ms ease";

        successFadeTimer = setTimeout(function () {
            successFadeTimer = null;
            el.textContent = "";
            el.className = "message";
            el.style.opacity = "";
            el.style.transition = "";
        }, MESSAGE_FADE_MS);
    }, effectiveDuration);
}

function clearMessage() {
    cancelSuccessTimers();
    var el = document.getElementById("message");
    if (!el) return;
    el.textContent = "";
    el.className = "message";
    el.style.opacity = "";
    el.style.transition = "";
}

function formatApiErrors(data) {
    if (!data || typeof data !== "object") return "Something went wrong.";
    var parts = [];
    if (Array.isArray(data)) {
        parts = data.map(String);
    } else if (data.non_field_errors) {
        parts = data.non_field_errors;
    } else {
        Object.keys(data).forEach(function (key) {
            var val = data[key];
            var label = key.replace(/_/g, " ");
            if (Array.isArray(val)) parts.push(label + ": " + val.join(" "));
            else parts.push(label + ": " + String(val));
        });
    }
    return parts.length ? parts.join(" ") : "Something went wrong.";
}

function fillDimensionList(id, items, nameKey, idKey, map) {
    var list = document.getElementById(id);
    if (!list) return;
    list.innerHTML = "";
    (items || []).forEach(function (item) {
        var opt = document.createElement("option");
        opt.value = item[nameKey];
        list.appendChild(opt);
        if (map) map[item[nameKey]] = item[idKey];
    });
}

function loadOptions() {
    var headers = getAuthHeaders();
    if (!headers) {
        showMessage("Please log in to log workouts.", "error");
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
            showMessage("Could not load exercise/attachment/equipment lists.", "error");
        });
}

/**
 * @param {{ silent?: boolean }} [options]
 *   silent: if true, only updates workout number input — no "6 hours elapsed" toast.
 */
function loadWorkoutNumber(options) {
    var silent = options && options.silent === true;
    var headers = getAuthHeaders();
    if (!headers) return;

    fetch(API_BASE + "/api/workouts/next-workout-info/", { headers: headers })
        .then(function (res) {
            return res.ok ? res.json() : null;
        })
        .then(function (data) {
            if (!data) return;
            var input = document.getElementById("workout_number");
            if (input) input.value = data.next_workout_number;

            if (!silent && data.hour_elapsed) {
                showMessage(
                    "Over 6 hours since last input — starting workout #" + data.next_workout_number + ".",
                    "success"
                );
            }
        })
        .catch(function () {});
}

function setDefaultDate() {
    var dateInput = document.getElementById("date");
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().slice(0, 10);
    }
}

function getPayload() {
    var dateVal = document.getElementById("date").value;
    var exerciseName = (document.getElementById("exercise_name").value || "").trim();
    var attachmentName = (document.getElementById("attachment_name").value || "").trim() || "None";
    var equipmentName = (document.getElementById("equipment_name").value || "").trim() || "None";

    return {
        exercise: exerciseMap[exerciseName] || null,
        attachment: attachmentMap[attachmentName] || attachmentMap["None"] || null,
        equipment: equipmentMap[equipmentName] || equipmentMap["None"] || null,
        workout_number: parseInt(document.getElementById("workout_number").value, 10) || 1,
        set_number: parseInt(document.getElementById("set_number").value, 10) || 1,
        repetitions: parseInt(document.getElementById("repetitions").value, 10) || 0,
        load: parseFloat(document.getElementById("load").value) || 0,
        unit: document.getElementById("unit").value || "KG",
        set_type: (document.getElementById("set_type").value || "").trim() || "Working set",
        comments: (document.getElementById("comments").value || "").trim() || "None",
        workout_split: (document.getElementById("workout_split").value || "").trim() || "None",
        date: dateVal || new Date().toISOString().slice(0, 10),
    };
}

function onSubmit(e) {
    e.preventDefault();
    clearMessage();
    var headers = getAuthHeaders();
    if (!headers) {
        showMessage("Please log in to log workouts.", "error");
        return;
    }
    var btn = document.getElementById("submit-btn");
    btn.disabled = true;
    fetch(API_BASE + "/api/workouts/", {
        method: "POST",
        headers: headers,
        body: JSON.stringify(getPayload()),
    })
        .then(function (res) {
            return res.json().then(function (data) {
                return { status: res.status, data: data };
            });
        })
        .then(function (result) {
            if (result.status >= 200 && result.status < 300) {
                showMessage("Workout saved.", "success");
                document.getElementById("set_number").value =
                    (parseInt(document.getElementById("set_number").value, 10) || 1) + 1;
                document.getElementById("repetitions").value = "0";
                document.getElementById("load").value = "0";
                document.getElementById("comments").value = "";
            } else {
                showMessage(formatApiErrors(result.data), "error");
            }
        })
        .catch(function () {
            showMessage("Network error. Try again.", "error");
        })
        .finally(function () {
            btn.disabled = false;
        });
}

function onDeleteLast() {
    clearMessage();
    var headers = getAuthHeaders();
    if (!headers) {
        showMessage("Please log in first.", "error");
        return;
    }
    var btn = document.getElementById("delete-last-btn");
    if (btn) btn.disabled = true;

    fetch(API_BASE + "/api/workouts/last/", {
        method: "DELETE",
        headers: headers,
    })
        .then(function (res) {
            return res.json().then(function (data) {
                return { status: res.status, data: data };
            });
        })
        .then(function (result) {
            if (result.status === 200 && result.data && result.data.message) {
                showMessage(result.data.message, "success", DELETE_SUCCESS_MS);
                var input = document.getElementById("workout_number");
                if (input && result.data.next_workout_number != null) {
                    input.value = result.data.next_workout_number;
                } else {
                    loadWorkoutNumber({ silent: true });
                }
                return;
            }
            if (result.status === 404) {
                showMessage(
                    (result.data && result.data.detail) || "No workouts to delete.",
                    "error"
                );
                return;
            }
            showMessage(formatApiErrors(result.data), "error");
        })
        .catch(function () {
            showMessage("Could not delete last entry.", "error");
        })
        .finally(function () {
            if (btn) btn.disabled = false;
        });
}

function initNumberInputs() {
    var ids = ["set_number", "repetitions", "load"];
    ids.forEach(function (id) {
        var input = document.getElementById(id);
        if (!input) return;
        input.addEventListener("focus", function () {
            if (this.value === "0" || this.value === "0.0") this.value = "";
        });
        input.addEventListener("blur", function () {
            if (this.value === "" || this.value == null) {
                var min = parseInt(this.getAttribute("min"), 10);
                this.value = isNaN(min) ? "0" : String(min);
            }
        });
    });
}

function initExerciseChangeResetSet() {
    var exerciseInput = document.getElementById("exercise_name");
    var setInput = document.getElementById("set_number");
    if (exerciseInput && setInput) {
        exerciseInput.addEventListener("change", function () {
            setInput.value = "1";
        });
    }
}

document.addEventListener("DOMContentLoaded", function () {
    setDefaultDate();
    loadOptions();
    loadWorkoutNumber();
    initNumberInputs();
    initExerciseChangeResetSet();
    document.getElementById("workout-form").addEventListener("submit", onSubmit);
    document.getElementById("delete-last-btn").addEventListener("click", onDeleteLast);
});
