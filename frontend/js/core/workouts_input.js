// Log Workout page — form wiring, API calls, and session helpers for fast gym-floor entry.
//
// Workout # and set # are read-only (filled from the API). Attachment/equipment are
// remembered per exercise name in sessionStorage for superset logging. Editable fields
// clear on focus so you can re-type without backspacing.

// Use localhost/127/::1 if running locally, otherwise use current host
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

/** Sentinel FK for optional attachment/equipment (matches backend PLACEHOLDER_DIMENSION_ID). */
var PLACEHOLDER_DIMENSION_ID = -1;

/** sessionStorage key: { [exerciseName]: { attachment_name, equipment_name } } */
var STICKY_STORAGE_KEY = "gym_sticky_by_exercise";

/** Last exercise name in the form; used to save gear before switching exercises. */
var activeExerciseName = "";

/**
 * Editable fields that clear on focus. emptyDefault is restored on blur when left blank.
 * Read-only, date, and select fields are intentionally excluded.
 */
var CLEAR_ON_FOCUS_FIELDS = {
    exercise_name: {},
    attachment_name: {},
    equipment_name: {},
    workout_split: {},
    repetitions: { emptyDefault: "0" },
    load: { emptyDefault: "0" },
    set_type: { emptyDefault: "Working set" },
    comments: {},
};

/** Default time before success messages fade (ms). */
var DEFAULT_SUCCESS_MS = 3500;
/** Delete-last confirmation: keep visible longer (5–10s range). */
var DELETE_SUCCESS_MS = 7500;
var MESSAGE_FADE_MS = 300;
var MESSAGE_MIN_MS = 1000;

/** Cleared when a new success message is shown so old timers do not clear the new text. */
var successHideTimer = null;
var successFadeTimer = null;

// --- Auth & user feedback ---

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

    var defaultDuration = type === "success" ? DEFAULT_SUCCESS_MS : DEFAULT_SUCCESS_MS;
    var effectiveDuration = Math.max(
        duration != null ? duration : defaultDuration,
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

var FIELD_LABELS = {
    repetitions: "Reps",
    set_number: "Set",
    load: "Load",
    exercise: "Exercise",
    equipment: "Equipment",
    attachment: "Attachment",
    workout_split: "Split",
    set_type: "Set type",
    unit: "Unit",
    date_id: "Date",
};

var WORKOUT_ERROR_MESSAGES = {
    repetitions: {
        "Ensure this value is greater than or equal to 1.": "Reps must be at least 1.",
        "This field is required.": "Reps are required.",
    },
    set_number: {
        "Ensure this value is greater than or equal to 1.": "Set number must be at least 1.",
        "This field is required.": "Set number is required.",
    },
    load: {
        "This field is required.": "Load is required.",
    },
};

function humanizeWorkoutError(key, message) {
    var mapped = WORKOUT_ERROR_MESSAGES[key] && WORKOUT_ERROR_MESSAGES[key][message];
    if (mapped) return mapped;
    var label = FIELD_LABELS[key] || key.replace(/_/g, " ");
    if (/greater than or equal to 1/i.test(message)) {
        return label + " must be at least 1.";
    }
    if (/required/i.test(message)) {
        return label + " is required.";
    }
    return label + ": " + message;
}

function formatApiErrors(data) {
    if (!data || typeof data !== "object") return "Something went wrong.";
    var parts = [];
    if (Array.isArray(data)) {
        parts = data.map(String);
    } else if (data.non_field_errors) {
        parts = data.non_field_errors.map(String);
    } else if (data.detail) {
        parts = [String(data.detail)];
    } else {
        Object.keys(data).forEach(function (key) {
            var val = data[key];
            var messages = Array.isArray(val) ? val : [String(val)];
            messages.forEach(function (msg) {
                parts.push(humanizeWorkoutError(key, msg));
            });
        });
    }
    return parts.length ? parts.join(" ") : "Something went wrong.";
}

// --- Dimension datalists (exercise, attachment, equipment) ---

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

// --- Per-exercise sticky attachment/equipment (sessionStorage) ---

function loadStickyMap() {
    try {
        var raw = sessionStorage.getItem(STICKY_STORAGE_KEY);
        return raw ? JSON.parse(raw) : {};
    } catch (e) {
        return {};
    }
}

function saveStickyMap(map) {
    try {
        sessionStorage.setItem(STICKY_STORAGE_KEY, JSON.stringify(map));
    } catch (e) {}
}

/** Prefill attachment/equipment from session memory for the given exercise. */
function applyStickyForExercise(exerciseName) {
    var attachmentInput = document.getElementById("attachment_name");
    var equipmentInput = document.getElementById("equipment_name");
    if (!attachmentInput || !equipmentInput) return;

    var sticky = loadStickyMap()[exerciseName];
    if (sticky) {
        attachmentInput.value =
            sticky.attachment_name && sticky.attachment_name !== "None" ? sticky.attachment_name : "";
        equipmentInput.value =
            sticky.equipment_name && sticky.equipment_name !== "None" ? sticky.equipment_name : "";
    } else {
        attachmentInput.value = "";
        equipmentInput.value = "";
    }
}

/** Persist the current form's attachment/equipment under the active exercise name. */
function saveStickyForCurrentExercise() {
    var exerciseName = (document.getElementById("exercise_name").value || "").trim();
    if (!exerciseName) return;
    var attachmentName = (document.getElementById("attachment_name").value || "").trim() || "None";
    var equipmentName = (document.getElementById("equipment_name").value || "").trim() || "None";
    saveStickyForExercise(exerciseName, attachmentName, equipmentName);
}

/** Before switching exercises, store gear for the exercise we're leaving. */
function saveStickyBeforeExerciseSwitch(nextExerciseName) {
    if (!activeExerciseName || activeExerciseName === nextExerciseName) return;
    var attachmentName = (document.getElementById("attachment_name").value || "").trim() || "None";
    var equipmentName = (document.getElementById("equipment_name").value || "").trim() || "None";
    saveStickyForExercise(activeExerciseName, attachmentName, equipmentName);
}

function saveStickyForExercise(exerciseName, attachmentName, equipmentName) {
    if (!exerciseName) return;
    var map = loadStickyMap();
    map[exerciseName] = {
        attachment_name: attachmentName || "None",
        equipment_name: equipmentName || "None",
    };
    saveStickyMap(map);
}

// --- Auto workout #, set #, and session split (API) ---

function resolveExerciseIdFromInput() {
    var exerciseName = (document.getElementById("exercise_name").value || "").trim();
    return exerciseMap[exerciseName] || null;
}

/** Fetch and display the next set # (and workout #) for the selected exercise. */
function loadNextSetNumber(exerciseId) {
    var headers = getAuthHeaders();
    var setInput = document.getElementById("set_number");
    if (!headers || !exerciseId || !setInput) return;

    fetch(API_BASE + "/api/workouts/next-set-info/?exercise_id=" + encodeURIComponent(exerciseId), {
        headers: headers,
    })
        .then(function (res) {
            return res.ok ? res.json() : null;
        })
        .then(function (data) {
            if (!data) return;
            setInput.value = data.next_set_number;
            var workoutInput = document.getElementById("workout_number");
            if (workoutInput && data.workout_number != null) {
                workoutInput.value = data.workout_number;
            }
        })
        .catch(function () {});
}

/** Exercise change: save previous exercise gear, restore this exercise's gear, refresh set #. */
function onExerciseFieldChange() {
    var exerciseName = (document.getElementById("exercise_name").value || "").trim();
    saveStickyBeforeExerciseSwitch(exerciseName);
    activeExerciseName = exerciseName;
    applyStickyForExercise(exerciseName);
    var exerciseId = resolveExerciseIdFromInput();
    if (exerciseId) {
        loadNextSetNumber(exerciseId);
    }
}

/**
 * Load workout # from the API and soft-default split from the current session.
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

            var splitInput = document.getElementById("workout_split");
            if (
                splitInput &&
                !(splitInput.value || "").trim() &&
                data.workout_split &&
                data.workout_split !== "None"
            ) {
                splitInput.value = data.workout_split;
            }

            if (!silent && data.hour_elapsed) {
                showMessage(
                    "Over 6 hours since last input — starting workout #" + data.next_workout_number + ".",
                    "success"
                );
            }
        })
        .catch(function () {});
}

function dimensionIdFromName(map, name) {
    if (map[name] != null) return map[name];
    if (name === "None") return PLACEHOLDER_DIMENSION_ID;
    return null;
}

function setDefaultDate() {
    var dateInput = document.getElementById("date");
    if (!dateInput) return;
    var today = new Date().toISOString().slice(0, 10);
    dateInput.max = today;
    if (!dateInput.value) {
        dateInput.value = today;
    }
}

// --- Form payload & submit ---

function getPayload() {
    var dateVal = document.getElementById("date").value;
    var today = new Date().toISOString().slice(0, 10);
    if (dateVal > today) {
        showMessage("Workout date cannot be in the future.", "error");
        return null;
    }
    var exerciseName = (document.getElementById("exercise_name").value || "").trim();
    var attachmentName = (document.getElementById("attachment_name").value || "").trim() || "None";
    var equipmentName = (document.getElementById("equipment_name").value || "").trim() || "None";

    return {
        exercise: exerciseMap[exerciseName] || null,
        attachment: dimensionIdFromName(attachmentMap, attachmentName),
        equipment: dimensionIdFromName(equipmentMap, equipmentName),
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
    var payload = getPayload();
    if (!payload) return;

    var btn = document.getElementById("submit-btn");
    btn.disabled = true;
    fetch(API_BASE + "/api/workouts/", {
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
                var exerciseName = (document.getElementById("exercise_name").value || "").trim();
                var attachmentName =
                    (document.getElementById("attachment_name").value || "").trim() || "None";
                var equipmentName =
                    (document.getElementById("equipment_name").value || "").trim() || "None";
                saveStickyForExercise(exerciseName, attachmentName, equipmentName);
                activeExerciseName = exerciseName;

                var saved = result.data || {};
                var workoutNum = saved.workout_number != null ? saved.workout_number : "?";
                var setNum = saved.set_number != null ? saved.set_number : "?";
                showMessage(
                    "Saved: " + exerciseName + " — Workout #" + workoutNum + ", Set " + setNum + ".",
                    "success"
                );

                if (saved.workout_number != null) {
                    document.getElementById("workout_number").value = saved.workout_number;
                }
                if (saved.exercise) {
                    loadNextSetNumber(saved.exercise);
                }

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
                var exerciseId = resolveExerciseIdFromInput();
                if (exerciseId) {
                    loadNextSetNumber(exerciseId);
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

// --- Form UX: clear-on-focus, exercise/gear handlers ---

function initClearOnFocus() {
    Object.keys(CLEAR_ON_FOCUS_FIELDS).forEach(function (id) {
        var input = document.getElementById(id);
        if (!input) return;
        var cfg = CLEAR_ON_FOCUS_FIELDS[id];

        input.addEventListener("focus", function () {
            if ((this.value || "").trim() !== "") {
                this.value = "";
            }
        });

        if (cfg.emptyDefault != null) {
            input.addEventListener("blur", function () {
                if ((this.value || "").trim() === "") {
                    this.value = cfg.emptyDefault;
                }
            });
        }
    });
}

function initExerciseChangeHandlers() {
    var exerciseInput = document.getElementById("exercise_name");
    if (!exerciseInput) return;
    exerciseInput.addEventListener("change", onExerciseFieldChange);
    exerciseInput.addEventListener("blur", onExerciseFieldChange);
}

/** Keep sticky map in sync when attachment/equipment are edited in place. */
function initGearStickyHandlers() {
    ["attachment_name", "equipment_name"].forEach(function (id) {
        var input = document.getElementById(id);
        if (!input) return;
        input.addEventListener("change", saveStickyForCurrentExercise);
        input.addEventListener("blur", saveStickyForCurrentExercise);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    setDefaultDate();
    loadOptions();
    loadWorkoutNumber();
    initClearOnFocus();
    initExerciseChangeHandlers();
    initGearStickyHandlers();
    document.getElementById("workout-form").addEventListener("submit", onSubmit);
    document.getElementById("delete-last-btn").addEventListener("click", onDeleteLast);
});
