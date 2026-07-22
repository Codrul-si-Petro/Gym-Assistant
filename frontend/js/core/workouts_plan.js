// Plan Workout page — build full workouts and schedule with recurrence.

var exerciseMap = {};
var attachmentMap = {};
var equipmentMap = {};
var exerciseBlocks = [];
var blockIdCounter = 0;
var editingSeriesId = null;

var WEEKDAY_CODES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];
var MAX_PLAN_SPAN_DAYS = 365;
var MAX_OCCURRENCES = 366;

var messageHideTimer = null;

function showMessage(text, type) {
    var el = document.getElementById("message");
    if (!el) return;
    if (messageHideTimer !== null) {
        clearTimeout(messageHideTimer);
        messageHideTimer = null;
    }
    el.textContent = text;
    el.className = "message " + (type === "success" ? "success" : "error");
    el.removeAttribute("hidden");
    if (type === "success") {
        messageHideTimer = setTimeout(clearMessage, 4000);
    }
}

function clearMessage() {
    var el = document.getElementById("message");
    if (!el) return;
    if (messageHideTimer !== null) {
        clearTimeout(messageHideTimer);
        messageHideTimer = null;
    }
    el.setAttribute("hidden", "hidden");
    el.textContent = "";
}

function todayIso() {
    // Use local date parts, not toISOString() (which is UTC and rolls back to
    // "yesterday" for anyone east of UTC during early-morning local hours).
    var d = new Date();
    var year = d.getFullYear();
    var month = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return year + "-" + month + "-" + day;
}

function addDaysIso(iso, days) {
    var d = new Date(iso + "T12:00:00");
    d.setDate(d.getDate() + days);
    return d.toISOString().slice(0, 10);
}

function weekdayIso(iso) {
    return new Date(iso + "T12:00:00").getDay();
}

function weekdayCodeFromIso(iso) {
    var map = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
    return map[weekdayIso(iso)];
}

function defaultSet() {
    return {
        reps: 0,
        load: 0,
        unit: "KG",
        equipmentName: "",
        attachmentName: "",
        setType: "Working set",
    };
}

function createBlock() {
    blockIdCounter += 1;
    return {
        id: blockIdCounter,
        exerciseName: "",
        sets: [defaultSet()],
    };
}

function getRepeatType() {
    var checked = document.querySelector('input[name="repeat_type"]:checked');
    return checked ? checked.value : "once";
}

function getSelectedWeekdays() {
    return Array.prototype.slice
        .call(document.querySelectorAll("#weekday_picker input:checked"))
        .map(function (el) {
            return el.value;
        });
}

function getRecurrenceFromForm() {
    var type = getRepeatType();
    var startDate = document.getElementById("plan_start_date").value;
    var endDate = document.getElementById("plan_end_date").value;
    if (!startDate) return null;
    if (type === "once") {
        return { type: "once", start_date: startDate, end_date: startDate };
    }
    if (!endDate) return null;
    var recurrence = { type: type, start_date: startDate, end_date: endDate };
    if (type === "weekly") {
        recurrence.weekdays = getSelectedWeekdays();
    } else if (type === "interval") {
        recurrence.interval_days = parseInt(document.getElementById("plan_interval_days").value, 10) || 1;
    }
    return recurrence;
}

function expandRecurrence(recurrence) {
    if (!recurrence || !recurrence.start_date) return [];
    var start = recurrence.start_date;
    var end = recurrence.end_date || start;
    if (end < start) return [];
    var span = Math.floor((new Date(end + "T12:00:00") - new Date(start + "T12:00:00")) / 86400000);
    if (span > MAX_PLAN_SPAN_DAYS) return [];

    if (recurrence.type === "once") return [start];

    var dates = [];
    if (recurrence.type === "weekly") {
        var weekdayToIso = { MON: 1, TUE: 2, WED: 3, THU: 4, FRI: 5, SAT: 6, SUN: 0 };
        var targets = {};
        (recurrence.weekdays || []).forEach(function (code) {
            targets[weekdayToIso[code]] = true;
        });
        var current = start;
        while (current <= end) {
            if (targets[weekdayIso(current)]) dates.push(current);
            current = addDaysIso(current, 1);
        }
        return dates.slice(0, MAX_OCCURRENCES);
    }

    if (recurrence.type === "interval") {
        var step = recurrence.interval_days || 1;
        var d = start;
        while (d <= end) {
            dates.push(d);
            d = addDaysIso(d, step);
        }
        return dates.slice(0, MAX_OCCURRENCES);
    }
    return [];
}

function totalSets() {
    return exerciseBlocks.reduce(function (sum, block) {
        return sum + block.sets.length;
    }, 0);
}

function updateRepeatUi() {
    var type = getRepeatType();
    document.getElementById("weekday_picker").hidden = type !== "weekly";
    document.getElementById("interval_picker").hidden = type !== "interval";
    document.getElementById("end_date_field").hidden = type === "once";
    updatePreview();
}

function updateEndDateMax() {
    var start = document.getElementById("plan_start_date").value;
    var endEl = document.getElementById("plan_end_date");
    if (!start) return;
    endEl.min = start;
    endEl.max = addDaysIso(start, MAX_PLAN_SPAN_DAYS);
    if (endEl.value && endEl.value > endEl.max) endEl.value = endEl.max;
    if (endEl.value && endEl.value < start) endEl.value = start;
}

function updatePreview() {
    var summary = document.getElementById("plan_preview_summary");
    var list = document.getElementById("plan_preview_dates");
    if (!summary || !list) return;

    var recurrence = getRecurrenceFromForm();
    var dates = expandRecurrence(recurrence);
    var sets = totalSets();
    var exercises = exerciseBlocks.filter(function (b) {
        return exerciseMap[b.exerciseName];
    }).length;

    list.replaceChildren();
    if (!recurrence) {
        summary.textContent = "Pick a start date to preview your plan.";
        return;
    }
    if (getRepeatType() === "weekly" && getSelectedWeekdays().length === 0) {
        summary.textContent = "Select at least one weekday.";
        return;
    }
    if (getRepeatType() !== "once" && !recurrence.end_date) {
        summary.textContent = "Pick an end date for your repeating plan.";
        return;
    }
    if (dates.length === 0) {
        summary.textContent = "No dates match this schedule in the selected range.";
        return;
    }

    summary.textContent =
        dates.length +
        " workout day" +
        (dates.length === 1 ? "" : "s") +
        ", " +
        exercises +
        " exercise" +
        (exercises === 1 ? "" : "s") +
        ", " +
        sets +
        " set" +
        (sets === 1 ? "" : "s") +
        " per day (" +
        dates.length * sets +
        " total set rows).";

    dates.slice(0, 14).forEach(function (d) {
        var li = document.createElement("li");
        li.textContent = d;
        list.appendChild(li);
    });
    if (dates.length > 14) {
        var more = document.createElement("li");
        more.textContent = "+" + (dates.length - 14) + " more";
        more.className = "plan-preview-more";
        list.appendChild(more);
    }
}

function renderSetRow(block, setIndex) {
    var set = block.sets[setIndex];
    return (
        '<div class="plan-set-row" data-set-index="' +
        setIndex +
        '">' +
        '<span class="plan-set-label">Set ' +
        (setIndex + 1) +
        "</span>" +
        '<input type="number" class="set-reps" min="1" max="1000" placeholder="Reps" value="' +
        set.reps +
        '" aria-label="Reps">' +
        '<input type="number" class="set-load" min="0" max="1500" step="any" placeholder="Load" value="' +
        set.load +
        '" aria-label="Load">' +
        '<select class="set-unit" aria-label="Unit"><option value="KG"' +
        (set.unit === "KG" ? " selected" : "") +
        '>KG</option><option value="LBS"' +
        (set.unit === "LBS" ? " selected" : "") +
        '>LBS</option></select>' +
        '<input type="text" class="set-equipment" list="equipment_list" value="' +
        (set.equipmentName || "") +
        '" placeholder="Equipment" aria-label="Equipment">' +
        '<input type="text" class="set-attachment" list="attachments_list" value="' +
        (set.attachmentName || "") +
        '" placeholder="Attachment" aria-label="Attachment">' +
        '<input type="text" class="set-type" placeholder="Set type" value="' +
        (set.setType || "Working set") +
        '" aria-label="Set type">' +
        '<button type="button" class="plan-icon-btn remove-set" aria-label="Remove set">×</button>' +
        "</div>"
    );
}

var PLAN_SET_HEADER_HTML =
    '<div class="plan-set-header" aria-hidden="true">' +
    "<span></span>" +
    "<span>Reps</span>" +
    "<span>Load</span>" +
    "<span>Unit</span>" +
    "<span>Equipment</span>" +
    "<span>Attachment</span>" +
    "<span>Type</span>" +
    "<span></span>" +
    "</div>";

function renderExerciseBlock(block) {
    var setsHtml = block.sets
        .map(function (_set, idx) {
            return renderSetRow(block, idx);
        })
        .join("");
    return (
        '<article class="plan-exercise-block" data-block-id="' +
        block.id +
        '">' +
        '<div class="plan-exercise-header">' +
        '<input type="text" class="exercise-name" list="exercises_list" value="' +
        (block.exerciseName || "") +
        '" placeholder="Exercise name" required aria-label="Exercise name">' +
        '<button type="button" class="plan-secondary-btn add-set">Add set</button>' +
        '<button type="button" class="plan-icon-btn remove-exercise" aria-label="Remove exercise">×</button>' +
        "</div>" +
        PLAN_SET_HEADER_HTML +
        '<div class="plan-sets">' +
        setsHtml +
        "</div>" +
        "</article>"
    );
}

function renderExercises() {
    var container = document.getElementById("exercises_container");
    if (!container) return;
    container.innerHTML = exerciseBlocks.map(renderExerciseBlock).join("");
    updatePreview();
}

function syncBlockFromDom(blockEl, block) {
    block.exerciseName = (blockEl.querySelector(".exercise-name").value || "").trim();
    var rows = Array.prototype.slice
        .call(blockEl.querySelectorAll(".plan-set-row"))
        .filter(function (row) {
            return row.querySelector(".set-reps") != null;
        });
    block.sets = rows.map(function (row) {
        return {
            reps: parseInt(row.querySelector(".set-reps").value, 10) || 1,
            load: parseFloat(row.querySelector(".set-load").value) || 0,
            unit: row.querySelector(".set-unit").value || "KG",
            equipmentName: (row.querySelector(".set-equipment").value || "").trim(),
            attachmentName: (row.querySelector(".set-attachment").value || "").trim(),
            setType: (row.querySelector(".set-type").value || "").trim() || "Working set",
        };
    });
}

function syncAllBlocksFromDom() {
    document.querySelectorAll(".plan-exercise-block").forEach(function (el) {
        var id = parseInt(el.getAttribute("data-block-id"), 10);
        var block = exerciseBlocks.find(function (b) {
            return b.id === id;
        });
        if (block) syncBlockFromDom(el, block);
    });
}

var MIN_REPS = 1;
var MAX_REPS = 1000;
var MIN_LOAD = 0;
var MAX_LOAD = 1500;

function buildPayload() {
    syncAllBlocksFromDom();
    var label = (document.getElementById("plan_label").value || "").trim();
    if (!label) {
        showMessage("Enter a plan name or split.", "error");
        return null;
    }

    var startDate = document.getElementById("plan_start_date").value;
    if (!startDate) {
        showMessage("Pick a start date.", "error");
        return null;
    }
    if (!editingSeriesId && startDate < todayIso()) {
        showMessage("Start date cannot be in the past.", "error");
        return null;
    }

    var recurrence = getRecurrenceFromForm();
    if (!recurrence) {
        showMessage("Pick a start date.", "error");
        return null;
    }
    if (getRepeatType() === "weekly" && getSelectedWeekdays().length === 0) {
        showMessage("Select at least one weekday.", "error");
        return null;
    }
    if (getRepeatType() !== "once" && !recurrence.end_date) {
        showMessage("Pick an end date for your repeating plan.", "error");
        return null;
    }
    if (getRepeatType() !== "once" && recurrence.end_date < recurrence.start_date) {
        showMessage("End date must be on or after the start date.", "error");
        return null;
    }
    if (exerciseBlocks.length === 0) {
        showMessage("Add at least one exercise.", "error");
        return null;
    }

    var seenExercises = {};
    var exercises = [];
    for (var i = 0; i < exerciseBlocks.length; i += 1) {
        var block = exerciseBlocks[i];
        var exerciseName = (block.exerciseName || "").trim();
        if (!exerciseName) {
            showMessage("Every exercise block needs an exercise name.", "error");
            return null;
        }
        if (!exerciseMap[exerciseName]) {
            showMessage('"' + exerciseName + '" is not a valid exercise. Pick one from the list.', "error");
            return null;
        }
        var exerciseId = exerciseMap[exerciseName];
        if (seenExercises[exerciseId]) {
            showMessage(
                '"' + exerciseName + '" is listed twice. Combine its sets into a single exercise block.',
                "error"
            );
            return null;
        }
        seenExercises[exerciseId] = true;

        if (!block.sets.length) {
            showMessage("Each exercise needs at least one set.", "error");
            return null;
        }

        var sets = [];
        for (var j = 0; j < block.sets.length; j += 1) {
            var set = block.sets[j];
            if (!isFinite(set.reps) || set.reps < MIN_REPS || set.reps > MAX_REPS) {
                showMessage(
                    exerciseName + " set " + (j + 1) + ": reps must be between " + MIN_REPS + " and " + MAX_REPS + ".",
                    "error"
                );
                return null;
            }
            if (!isFinite(set.load) || set.load < MIN_LOAD || set.load > MAX_LOAD) {
                showMessage(
                    exerciseName + " set " + (j + 1) + ": load must be between " + MIN_LOAD + " and " + MAX_LOAD + ".",
                    "error"
                );
                return null;
            }
            var equipmentName = set.equipmentName || "None";
            var attachmentName = set.attachmentName || "None";
            var equipmentId = dimensionIdFromName(equipmentMap, equipmentName);
            if (equipmentId == null) {
                showMessage(
                    exerciseName + " set " + (j + 1) + ': unknown equipment "' + equipmentName + '". Pick one from the list or leave blank.',
                    "error"
                );
                return null;
            }
            var attachmentId = dimensionIdFromName(attachmentMap, attachmentName);
            if (attachmentId == null) {
                showMessage(
                    exerciseName + " set " + (j + 1) + ': unknown attachment "' + attachmentName + '". Pick one from the list or leave blank.',
                    "error"
                );
                return null;
            }
            if (!(set.setType || "").trim()) {
                showMessage(exerciseName + " set " + (j + 1) + ": set type cannot be blank.", "error");
                return null;
            }
            sets.push({
                reps: set.reps,
                load: set.load,
                unit: set.unit,
                equipment: equipmentId === PLACEHOLDER_DIMENSION_ID ? null : equipmentId,
                attachment: attachmentId === PLACEHOLDER_DIMENSION_ID ? null : attachmentId,
                set_type: set.setType.trim(),
            });
        }

        exercises.push({ exercise: exerciseId, sets: sets });
    }

    return {
        label: label,
        description: (document.getElementById("plan_description")?.value || "").trim(),
        workout_split: (document.getElementById("plan_workout_split")?.value || "").trim(),
        recurrence: recurrence,
        exercises: exercises,
    };
}

function resetBuilder() {
    editingSeriesId = null;
    document.getElementById("plan_label").value = "";
    var descEl = document.getElementById("plan_description");
    if (descEl) descEl.value = "";
    var splitEl = document.getElementById("plan_workout_split");
    if (splitEl) splitEl.value = "";
    var startEl = document.getElementById("plan_start_date");
    startEl.min = todayIso();
    startEl.value = todayIso();
    document.getElementById("plan_end_date").value = "";
    document.querySelector('input[name="repeat_type"][value="once"]').checked = true;
    document.querySelectorAll("#weekday_picker input").forEach(function (el) {
        el.checked = false;
    });
    document.getElementById("plan_interval_days").value = "2";
    exerciseBlocks = [createBlock()];
    document.getElementById("cancel_edit_btn").hidden = true;
    document.getElementById("submit-btn").textContent = "Save plan";
    updateRepeatUi();
    updateEndDateMax();
    renderExercises();
}

function syncSplitChips(labelValue) {
    // Kept as no-op for older call sites; splits now come from profile datalist.
}

function loadUserSplitSuggestions() {
    var list = document.getElementById("user_split_suggestions");
    if (!list) return Promise.resolve();
    var headers = getAuthHeaders();
    if (!headers) return Promise.resolve();
    return fetch(API_BASE + "/api/auth/current-user/", { headers: headers })
        .then(function (res) {
            return res.ok ? res.json() : null;
        })
        .then(function (user) {
            var splits = (user && Array.isArray(user.workout_splits) ? user.workout_splits : []) || [];
            list.innerHTML = splits
                .map(function (name) {
                    return '<option value="' + String(name).replace(/"/g, "&quot;") + '"></option>';
                })
                .join("");
        })
        .catch(function () {
            list.innerHTML = "";
        });
}

function loadPlanIntoBuilder(plan) {
    editingSeriesId = plan.plan_series_id;
    document.getElementById("plan_label").value = plan.label || "";
    var descEl = document.getElementById("plan_description");
    if (descEl) descEl.value = plan.description || "";
    var splitEl = document.getElementById("plan_workout_split");
    if (splitEl) splitEl.value = plan.workout_split || "";
    var startEl = document.getElementById("plan_start_date");
    // Existing plans may have started in the past; relax min so the field
    // still displays/round-trips correctly while editing.
    if (plan.recurrence.start_date < todayIso()) startEl.min = plan.recurrence.start_date;
    else startEl.min = todayIso();
    startEl.value = plan.recurrence.start_date;
    document.getElementById("plan_end_date").value = plan.recurrence.end_date;
    document.querySelector('input[name="repeat_type"][value="' + plan.recurrence.type + '"]').checked = true;
    document.querySelectorAll("#weekday_picker input").forEach(function (el) {
        el.checked = (plan.recurrence.weekdays || []).indexOf(el.value) !== -1;
    });
    document.getElementById("plan_interval_days").value = plan.recurrence.interval_days || 2;

    exerciseBlocks = (plan.exercises || []).map(function (ex) {
        blockIdCounter += 1;
        var exerciseName = "";
        Object.keys(exerciseMap).forEach(function (name) {
            if (exerciseMap[name] === ex.exercise) exerciseName = name;
        });
        return {
            id: blockIdCounter,
            exerciseName: exerciseName,
            sets: (ex.sets || []).map(function (set) {
                var equipmentName = "None";
                var attachmentName = "None";
                Object.keys(equipmentMap).forEach(function (name) {
                    if (equipmentMap[name] === set.equipment) equipmentName = name;
                });
                Object.keys(attachmentMap).forEach(function (name) {
                    if (attachmentMap[name] === set.attachment) attachmentName = name;
                });
                if (set.equipment == null) equipmentName = "";
                if (set.attachment == null) attachmentName = "";
                return {
                    reps: set.reps,
                    load: set.load,
                    unit: set.unit || "KG",
                    equipmentName: equipmentName === "None" ? "" : equipmentName,
                    attachmentName: attachmentName === "None" ? "" : attachmentName,
                    setType: set.set_type || "Working set",
                };
            }),
        };
    });
    if (!exerciseBlocks.length) exerciseBlocks = [createBlock()];

    document.getElementById("cancel_edit_btn").hidden = false;
    document.getElementById("submit-btn").textContent = "Update plan";
    updateRepeatUi();
    updateEndDateMax();
    renderExercises();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Prefills the builder from an existing plan as a *new* plan (POST on save).
 * Resets the schedule so the user must pick the target day/recurrence.
 */
function duplicatePlanIntoBuilder(plan) {
    editingSeriesId = null;
    document.getElementById("plan_label").value = plan.label || "";
    var descEl = document.getElementById("plan_description");
    if (descEl) descEl.value = plan.description || "";
    var splitEl = document.getElementById("plan_workout_split");
    if (splitEl) splitEl.value = plan.workout_split || "";

    var startEl = document.getElementById("plan_start_date");
    startEl.min = todayIso();
    startEl.value = todayIso();
    document.getElementById("plan_end_date").value = "";
    document.querySelector('input[name="repeat_type"][value="once"]').checked = true;
    document.querySelectorAll("#weekday_picker input").forEach(function (el) {
        el.checked = false;
    });
    document.getElementById("plan_interval_days").value = "2";

    exerciseBlocks = (plan.exercises || []).map(function (ex) {
        blockIdCounter += 1;
        var exerciseName = "";
        Object.keys(exerciseMap).forEach(function (name) {
            if (exerciseMap[name] === ex.exercise) exerciseName = name;
        });
        return {
            id: blockIdCounter,
            exerciseName: exerciseName,
            sets: (ex.sets || []).map(function (set) {
                var equipmentName = "None";
                var attachmentName = "None";
                Object.keys(equipmentMap).forEach(function (name) {
                    if (equipmentMap[name] === set.equipment) equipmentName = name;
                });
                Object.keys(attachmentMap).forEach(function (name) {
                    if (attachmentMap[name] === set.attachment) attachmentName = name;
                });
                if (set.equipment == null) equipmentName = "";
                if (set.attachment == null) attachmentName = "";
                return {
                    reps: set.reps,
                    load: set.load,
                    unit: set.unit || "KG",
                    equipmentName: equipmentName === "None" ? "" : equipmentName,
                    attachmentName: attachmentName === "None" ? "" : attachmentName,
                    setType: set.set_type || "Working set",
                };
            }),
        };
    });
    if (!exerciseBlocks.length) exerciseBlocks = [createBlock()];

    document.getElementById("cancel_edit_btn").hidden = true;
    document.getElementById("submit-btn").textContent = "Save plan";
    updateRepeatUi();
    updateEndDateMax();
    renderExercises();
    showMessage("Copied. Pick the new day or schedule, then save.", "success");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function recurrenceSummary(plan) {
    var r = plan.recurrence;
    if (r.type === "once") return "Once on " + r.start_date;
    if (r.type === "weekly") {
        return "Every " + (r.weekdays || []).join(", ") + " until " + r.end_date;
    }
    return "Every " + (r.interval_days || 1) + " days until " + r.end_date;
}

function renderMyPlans(plans) {
    var container = document.getElementById("my_plans_list");
    if (!container) return;
    if (!plans.length) {
        container.innerHTML = '<p class="plan-empty">No saved plans yet.</p>';
        return;
    }
    container.innerHTML = plans
        .map(function (plan) {
            return (
                '<article class="my-plan-card" data-series-id="' +
                plan.plan_series_id +
                '">' +
                "<h3>" +
                plan.label +
                "</h3>" +
                '<p class="my-plan-meta">' +
                recurrenceSummary(plan) +
                "</p>" +
                '<p class="my-plan-meta">' +
                (plan.exercise_count || 0) +
                " exercises · " +
                (plan.set_count || 0) +
                " sets/day · " +
                (plan.occurrence_count || 0) +
                " days" +
                (plan.next_date ? " · next: " + plan.next_date : "") +
                "</p>" +
                '<div class="my-plan-actions">' +
                '<button type="button" class="plan-secondary-btn edit-plan">Edit</button>' +
                '<button type="button" class="plan-secondary-btn copy-plan">Copy</button>' +
                '<button type="button" class="plan-secondary-btn delete-plan-future">Delete future</button>' +
                '<button type="button" class="plan-danger-btn delete-plan-all">Delete all</button>' +
                "</div>" +
                "</article>"
            );
        })
        .join("");
}

function loadMyPlans() {
    var headers = getAuthHeaders();
    if (!headers) return Promise.resolve();
    return fetch(API_BASE + "/api/plan-series/", { headers: headers })
        .then(function (res) {
            return res.ok ? res.json() : [];
        })
        .then(renderMyPlans)
        .catch(function () {
            renderMyPlans([]);
        });
}

function flattenErrors(data) {
    var messages = [];
    if (data == null) return messages;
    if (typeof data === "string") {
        messages.push(data);
    } else if (Array.isArray(data)) {
        data.forEach(function (item) {
            messages = messages.concat(flattenErrors(item));
        });
    } else if (typeof data === "object") {
        Object.keys(data).forEach(function (key) {
            messages = messages.concat(flattenErrors(data[key]));
        });
    } else {
        messages.push(String(data));
    }
    return messages;
}

function errorMessageFromResponse(data) {
    var messages = flattenErrors(data);
    if (!messages.length) return "Could not save plan.";
    // De-dupe in case the same message appears under multiple keys.
    var seen = {};
    var unique = messages.filter(function (m) {
        if (seen[m]) return false;
        seen[m] = true;
        return true;
    });
    return unique.join(" ");
}

function onSubmit(e) {
    e.preventDefault();
    clearMessage();
    var headers = getAuthHeaders();
    if (!headers) {
        showMessage("Please log in first.", "error");
        return;
    }
    var payload = buildPayload();
    if (!payload) return;

    var btn = document.getElementById("submit-btn");
    btn.disabled = true;
    var url = API_BASE + "/api/plan-series/";
    var method = "POST";
    if (editingSeriesId) {
        url += editingSeriesId + "/";
        method = "PUT";
    }

    fetch(url, { method: method, headers: headers, body: JSON.stringify(payload) })
        .then(function (res) {
            return res.json().then(function (data) {
                return { status: res.status, data: data };
            });
        })
        .then(function (result) {
            if (result.status >= 200 && result.status < 300) {
                showMessage(editingSeriesId ? "Plan updated." : "Plan saved.", "success");
                resetBuilder();
                loadMyPlans();
            } else {
                showMessage(errorMessageFromResponse(result.data), "error");
            }
        })
        .catch(function () {
            showMessage("Network error. Try again.", "error");
        })
        .finally(function () {
            btn.disabled = false;
        });
}

function deletePlan(seriesId, scope) {
    var headers = getAuthHeaders();
    if (!headers) return;
    var msg =
        scope === "all"
            ? "Delete this plan and all its scheduled sets?"
            : "Delete all future occurrences of this plan?";
    if (!window.confirm(msg)) return;

    fetch(API_BASE + "/api/plan-series/" + seriesId + "/?scope=" + scope, {
        method: "DELETE",
        headers: headers,
    })
        .then(function (res) {
            if (res.ok) {
                showMessage("Plan deleted.", "success");
                if (editingSeriesId === seriesId) resetBuilder();
                loadMyPlans();
            } else {
                showMessage("Could not delete plan.", "error");
            }
        })
        .catch(function () {
            showMessage("Network error. Try again.", "error");
        });
}

document.addEventListener("DOMContentLoaded", function () {
    loadDimensionOptions(
        { exerciseMap: exerciseMap, attachmentMap: attachmentMap, equipmentMap: equipmentMap },
        {
            loginMessage: "Please log in to plan workouts.",
            loadErrorMessage: "Could not load exercise lists.",
        }
    ).then(function () {
        resetBuilder();
        loadUserSplitSuggestions();
        loadMyPlans();
    });

    document.querySelectorAll('input[name="repeat_type"]').forEach(function (el) {
        el.addEventListener("change", updateRepeatUi);
    });
    document.getElementById("weekday_picker").addEventListener("change", updatePreview);
    document.getElementById("plan_start_date").addEventListener("change", function () {
        updateEndDateMax();
        updatePreview();
    });
    document.getElementById("plan_end_date").addEventListener("change", updatePreview);
    document.getElementById("plan_interval_days").addEventListener("input", updatePreview);

    document.getElementById("add_exercise_btn").addEventListener("click", function () {
        syncAllBlocksFromDom();
        exerciseBlocks.push(createBlock());
        renderExercises();
    });

    document.getElementById("exercises_container").addEventListener("click", function (e) {
        var blockEl = e.target.closest(".plan-exercise-block");
        if (!blockEl) return;
        var blockId = parseInt(blockEl.getAttribute("data-block-id"), 10);
        var block = exerciseBlocks.find(function (b) {
            return b.id === blockId;
        });
        if (!block) return;

        if (e.target.classList.contains("remove-exercise")) {
            syncAllBlocksFromDom();
            exerciseBlocks = exerciseBlocks.filter(function (b) {
                return b.id !== blockId;
            });
            if (!exerciseBlocks.length) exerciseBlocks = [createBlock()];
            renderExercises();
            return;
        }

        if (e.target.classList.contains("add-set")) {
            syncBlockFromDom(blockEl, block);
            var prev = block.sets[block.sets.length - 1] || defaultSet();
            block.sets.push({
                reps: prev.reps,
                load: prev.load,
                unit: prev.unit,
                equipmentName: prev.equipmentName,
                attachmentName: prev.attachmentName,
                setType: prev.setType,
            });
            renderExercises();
            return;
        }

        if (e.target.classList.contains("remove-set")) {
            syncBlockFromDom(blockEl, block);
            var row = e.target.closest(".plan-set-row");
            var setIndex = parseInt(row.getAttribute("data-set-index"), 10);
            if (block.sets.length <= 1) return;
            block.sets.splice(setIndex, 1);
            renderExercises();
        }
    });

    document.getElementById("exercises_container").addEventListener("input", updatePreview);

    // Clear-on-focus / restore-on-blur, matching the log-workout form's fast-entry UX.
    // Delegated (via focusin/focusout, which bubble) since set rows are re-rendered often.
    var CLEAR_ON_FOCUS_DEFAULTS = {
        "set-reps": "0",
        "set-load": "0",
        "set-type": "Working set",
    };
    var CLEAR_ON_FOCUS_SELECTOR =
        ".exercise-name, .set-reps, .set-load, .set-equipment, .set-attachment, .set-type";
    document.getElementById("exercises_container").addEventListener("focusin", function (e) {
        var el = e.target;
        if (!el.matches || !el.matches(CLEAR_ON_FOCUS_SELECTOR)) return;
        if ((el.value || "").trim() !== "") el.value = "";
    });
    document.getElementById("exercises_container").addEventListener("focusout", function (e) {
        var el = e.target;
        if (!el.matches || !el.matches(CLEAR_ON_FOCUS_SELECTOR)) return;
        if ((el.value || "").trim() !== "") return;
        var cls = ["set-reps", "set-load", "set-type"].find(function (c) {
            return el.classList.contains(c);
        });
        if (cls) el.value = CLEAR_ON_FOCUS_DEFAULTS[cls];
    });

    document.getElementById("workout-plan-form").addEventListener("submit", onSubmit);
    document.getElementById("cancel_edit_btn").addEventListener("click", function () {
        resetBuilder();
        clearMessage();
    });

    document.getElementById("my_plans_list").addEventListener("click", function (e) {
        var card = e.target.closest(".my-plan-card");
        if (!card) return;
        var seriesId = card.getAttribute("data-series-id");
        if (e.target.classList.contains("edit-plan") || e.target.classList.contains("copy-plan")) {
            var asCopy = e.target.classList.contains("copy-plan");
            var headers = getAuthHeaders();
            if (!headers) return;
            fetch(API_BASE + "/api/plan-series/" + seriesId + "/", { headers: headers })
                .then(function (res) {
                    return res.ok ? res.json() : null;
                })
                .then(function (plan) {
                    if (!plan) {
                        showMessage("Could not load plan.", "error");
                        return;
                    }
                    if (asCopy) duplicatePlanIntoBuilder(plan);
                    else loadPlanIntoBuilder(plan);
                });
        } else if (e.target.classList.contains("delete-plan-future")) {
            deletePlan(seriesId, "future");
        } else if (e.target.classList.contains("delete-plan-all")) {
            deletePlan(seriesId, "all");
        }
    });
});
