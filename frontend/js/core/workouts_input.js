// Log Workout page — form wiring, API calls, and session helpers for fast gym-floor entry.
//
// Workout # and set # are read-only (filled from the API). Attachment/equipment are
// remembered per exercise name in sessionStorage for superset logging. Editable fields
// clear on focus so you can re-type without backspacing.

var exerciseMap = {};
var attachmentMap = {};
var equipmentMap = {};

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

function loadOptions() {
    return loadDimensionOptions(
        { exerciseMap: exerciseMap, attachmentMap: attachmentMap, equipmentMap: equipmentMap },
        {
            loginMessage: "Please log in to log workouts.",
            loadErrorMessage: "Could not load exercise/attachment/equipment lists.",
        }
    );
}

function renderBackToTodayLink() {
    var form = document.getElementById("workout-form");
    if (!form || document.getElementById("back-to-today-link")) return;
    var link = document.createElement("a");
    link.id = "back-to-today-link";
    link.className = "plan-return-link";
    link.href = "today.html";
    link.textContent = "← Back to today's workout";
    form.insertBefore(link, form.firstChild);
}

function isPlanFlowFromToday() {
    return new URLSearchParams(window.location.search).get("return_to") === "today";
}

function applyPlanRowToForm(exerciseId, row, split) {
    var exId = normalizePlanId(exerciseId);
    var exerciseName = dimensionNameFromId(exerciseMap, exId);
    if (!exerciseName) return false;

    var exerciseInput = document.getElementById("exercise_name");
    if (exerciseInput) {
        exerciseInput.value = exerciseName;
        onExerciseFieldChange();
    }

    var equipmentInput = document.getElementById("equipment_name");
    var attachmentInput = document.getElementById("attachment_name");
    var repsInput = document.getElementById("repetitions");
    var loadInput = document.getElementById("load");
    var unitInput = document.getElementById("unit");
    var setTypeInput = document.getElementById("set_type");
    var splitInput = document.getElementById("workout_split");

    if (equipmentInput) {
        var eqName = dimensionNameFromId(equipmentMap, row.equipment);
        equipmentInput.value = eqName && eqName !== "None" ? eqName : "";
    }
    if (attachmentInput) {
        var atName = dimensionNameFromId(attachmentMap, row.attachment);
        attachmentInput.value = atName && atName !== "None" ? atName : "";
    }
    if (repsInput) repsInput.value = String(row.repetitions);
    if (loadInput) loadInput.value = String(row.load);
    if (unitInput) unitInput.value = row.unit || "KG";
    if (setTypeInput) setTypeInput.value = row.set_type || "Working set";
    if (splitInput && split && split !== "None") splitInput.value = split;

    saveStickyForCurrentExercise();
    return true;
}

function applyPlanTargetToForm(target) {
    return applyPlanRowToForm(target.exerciseId, target.setRow, target.split);
}

function advancePlanFlowAfterSubmit() {
    if (!isPlanFlowFromToday()) return Promise.resolve(false);
    var params = new URLSearchParams(window.location.search);
    var exerciseId = normalizePlanId(parseInt(params.get("exercise_id"), 10));
    var setIndex = parseInt(params.get("set_index"), 10);
    if (!isFinite(setIndex)) setIndex = 1;

    return fetchWorkoutsForDate("plan", planTodayIso()).then(function (planRows) {
        var next = findNextPlanTargetAfter(planRows, exerciseId, setIndex, exerciseMap);
        if (!next) {
            window.location.href = "today.html";
            return true;
        }
        applyPlanTargetToForm(next);
        window.history.replaceState(null, "", "workouts_input.html?" + buildPlanLogQueryParams(next));
        showMessage("Saved. Next: " + next.exerciseName + " — set " + next.setIndex + ".", "success");
        return true;
    });
}

/** Prefill log form from query params when opened from Today's plan. */
function applyPlanPrefillFromQuery() {
    var params = new URLSearchParams(window.location.search);
    if (params.get("return_to") === "today") {
        renderBackToTodayLink();
    }

    var exerciseIdRaw = params.get("exercise_id");
    if (!exerciseIdRaw) return;

    var exerciseId = parseInt(exerciseIdRaw, 10);
    if (!isFinite(exerciseId)) return;

    var row = {
        repetitions: params.get("reps") || "0",
        load: params.get("load") || "0",
        unit: params.get("unit") || "KG",
        set_type: params.get("set_type") || "Working set",
        equipment: params.has("equipment_id") ? parseInt(params.get("equipment_id"), 10) : null,
        attachment: params.has("attachment_id") ? parseInt(params.get("attachment_id"), 10) : null,
    };
    var split = params.get("workout_split") || null;
    applyPlanRowToForm(exerciseId, row, split);
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

function setDefaultDate() {
    var dateInput = document.getElementById("date");
    if (!dateInput) return;
    var today = new Date().toISOString().slice(0, 10);
    dateInput.max = today;
    if (!dateInput.value) {
        dateInput.value = today;
    }
}

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
    if (!exerciseMap[exerciseName]) {
        showMessage("Pick a valid exercise from the list.", "error");
        return null;
    }

    return {
        exercise: exerciseMap[exerciseName],
        attachment: dimensionIdFromName(attachmentMap, attachmentName),
        equipment: dimensionIdFromName(equipmentMap, equipmentName),
        set_number: parseInt(document.getElementById("set_number").value, 10) || 1,
        repetitions: parseInt(document.getElementById("repetitions").value, 10) || 0,
        load: parseFloat(document.getElementById("load").value) || 0,
        unit: document.getElementById("unit").value || "KG",
        set_type: (document.getElementById("set_type").value || "").trim() || "Working set",
        comments: (document.getElementById("comments").value || "").trim() || "None",
        workout_split: (document.getElementById("workout_split").value || "").trim() || "None",
        date: dateVal || today,
    };
}

// --- Form payload & submit ---

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
                if (saved.workout_number != null) {
                    document.getElementById("workout_number").value = saved.workout_number;
                }

                if (isPlanFlowFromToday()) {
                    return advancePlanFlowAfterSubmit().then(function (advanced) {
                        if (!advanced) {
                            var workoutNum = saved.workout_number != null ? saved.workout_number : "?";
                            var setNum = saved.set_number != null ? saved.set_number : "?";
                            showMessage(
                                "Saved: " + exerciseName + " — Workout #" + workoutNum + ", Set " + setNum + ".",
                                "success"
                            );
                        }
                    });
                }

                var workoutNum = saved.workout_number != null ? saved.workout_number : "?";
                var setNum = saved.set_number != null ? saved.set_number : "?";
                showMessage(
                    "Saved: " + exerciseName + " — Workout #" + workoutNum + ", Set " + setNum + ".",
                    "success"
                );

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

function applyVoiceResult(parsed) {
    var exerciseInput = document.getElementById("exercise_name");
    var attachmentInput = document.getElementById("attachment_name");
    var equipmentInput = document.getElementById("equipment_name");
    var repsInput = document.getElementById("repetitions");
    var loadInput = document.getElementById("load");
    var unitInput = document.getElementById("unit");

    // Only touch the exercise field (and its sticky/next-set side effects) when this
    // dictation actually mentioned an exercise. Otherwise leave it — and the gear it
    // carries via sticky memory — untouched (e.g. "20 reps 30 kilos" for the next set
    // of the exercise already in the form shouldn't clear exercise/equipment/attachment).
    var newExerciseName = parsed.exercise || parsed.exerciseRaw || "";
    if (newExerciseName && exerciseInput) {
        exerciseInput.value = newExerciseName;
        onExerciseFieldChange();
    }

    if (equipmentInput) {
        if (parsed.equipmentForceClear) {
            equipmentInput.value = "";
        } else if (parsed.equipment) {
            equipmentInput.value = parsed.equipment;
        }
    }

    if (attachmentInput) {
        if (parsed.attachmentForceClear) {
            attachmentInput.value = "";
        } else if (parsed.attachment) {
            attachmentInput.value = parsed.attachment;
        }
    }

    if (repsInput && parsed.repetitions != null) {
        repsInput.value = String(parsed.repetitions);
    }
    if (loadInput && parsed.load != null) {
        loadInput.value = String(parsed.load);
    }
    if (unitInput && parsed.unit) {
        unitInput.value = parsed.unit;
    }

    saveStickyForCurrentExercise();
}

document.addEventListener("DOMContentLoaded", function () {
    setDefaultDate();
    loadWorkoutNumber();
    loadOptions().then(function () {
        applyPlanPrefillFromQuery();
    });
    initClearOnFocus();
    initExerciseChangeHandlers();
    initGearStickyHandlers();
    if (window.GymVoiceInput) {
        GymVoiceInput.init({
            getMaps: function () {
                return {
                    exerciseMap: exerciseMap,
                    equipmentMap: equipmentMap,
                    attachmentMap: attachmentMap,
                };
            },
            onParsed: applyVoiceResult,
            showError: function (message) {
                showMessage(message, "error");
            },
        });
    }
    document.getElementById("workout-form").addEventListener("submit", onSubmit);
    document.getElementById("delete-last-btn").addEventListener("click", onDeleteLast);
});
