// Shared helpers for following a planned workout (Today page + Log prefill/advance).

function planTodayIso() {
    var d = new Date();
    return (
        d.getFullYear() +
        "-" +
        String(d.getMonth() + 1).padStart(2, "0") +
        "-" +
        String(d.getDate()).padStart(2, "0")
    );
}

function parseWorkoutList(payload) {
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload.results)) return payload.results;
    return [];
}

function fetchWorkoutsForDate(scenario, dateIso) {
    var headers = getAuthHeaders();
    if (!headers) return Promise.resolve([]);
    var url =
        API_BASE +
        "/api/workouts/?scenario=" +
        encodeURIComponent(scenario) +
        "&start_date=" +
        encodeURIComponent(dateIso) +
        "&end_date=" +
        encodeURIComponent(dateIso) +
        "&page_size=200";
    return fetch(url, { headers: headers })
        .then(function (res) {
            return res.ok ? res.json() : null;
        })
        .then(parseWorkoutList)
        .catch(function () {
            return [];
        });
}

function countActualsByExercise(actualRows) {
    var counts = {};
    actualRows.forEach(function (row) {
        var exId = normalizePlanId(row.exercise);
        counts[exId] = (counts[exId] || 0) + 1;
    });
    return counts;
}

function normalizePlanId(value) {
    if (value == null) return null;
    var n = parseInt(value, 10);
    return isFinite(n) ? n : value;
}

function minWorkoutId(rows) {
    var min = null;
    rows.forEach(function (row) {
        var id = row.workout_id;
        if (id == null) return;
        if (min == null || id < min) min = id;
    });
    return min == null ? 0 : min;
}

/** Preserve plan-builder exercise order (API list order is not stable). */
function sortExerciseIdsByPlanSequence(exerciseOrder, exercises) {
    return exerciseOrder.slice().sort(function (a, b) {
        return minWorkoutId(exercises[a]) - minWorkoutId(exercises[b]);
    });
}

/** Flat ordered list of planned set targets for a day. */
function buildPlanTargets(planRows) {
    var groups = {};
    var groupOrder = [];

    planRows.forEach(function (row) {
        var groupKey = row.plan_group_id || "legacy-" + row.workout_split;
        if (!groups[groupKey]) {
            groups[groupKey] = { exerciseOrder: [], exercises: {} };
            groupOrder.push(groupKey);
        }
        var g = groups[groupKey];
        var exId = normalizePlanId(row.exercise);
        if (!g.exercises[exId]) {
            g.exercises[exId] = [];
            g.exerciseOrder.push(exId);
        }
        g.exercises[exId].push(row);
    });

    var targets = [];
    groupOrder.forEach(function (groupKey) {
        var g = groups[groupKey];
        sortExerciseIdsByPlanSequence(g.exerciseOrder, g.exercises).forEach(function (exId) {
            var sets = g.exercises[exId].slice().sort(function (a, b) {
                return a.set_number - b.set_number;
            });
            sets.forEach(function (setRow, idx) {
                targets.push({
                    exerciseId: exId,
                    setIndex: idx + 1,
                    setRow: setRow,
                    split: setRow.workout_split,
                });
            });
        });
    });
    return targets;
}

function findNextPlanTarget(planRows, actualRows, exerciseMap) {
    var actualCounts = countActualsByExercise(actualRows);
    var targets = buildPlanTargets(planRows);

    for (var i = 0; i < targets.length; i += 1) {
        var t = targets[i];
        var logged = actualCounts[t.exerciseId] || 0;
        if (logged < t.setIndex) {
            return targetFromPlanRow(t, exerciseMap);
        }
    }
    return null;
}

function targetFromPlanRow(t, exerciseMap) {
    return {
        exerciseId: t.exerciseId,
        exerciseName:
            dimensionNameFromId(exerciseMap, t.exerciseId) || "Exercise #" + t.exerciseId,
        setIndex: t.setIndex,
        setRow: t.setRow,
        split: t.split,
    };
}

/** Next planned set after the one just logged (does not rely on actuals API). */
function findNextPlanTargetAfter(planRows, exerciseId, setIndex, exerciseMap) {
    var targets = buildPlanTargets(planRows);
    var exId = normalizePlanId(exerciseId);
    var idx = parseInt(setIndex, 10);
    if (!isFinite(idx)) idx = 1;

    for (var i = 0; i < targets.length; i += 1) {
        var t = targets[i];
        if (t.exerciseId === exId && t.setIndex === idx) {
            var next = targets[i + 1];
            return next ? targetFromPlanRow(next, exerciseMap) : null;
        }
    }
    return null;
}

function buildPlanLogQueryParams(target) {
    var row = target.setRow;
    var params = new URLSearchParams();
    params.set("exercise_id", String(target.exerciseId));
    if (target.setIndex != null) params.set("set_index", String(target.setIndex));
    params.set("reps", String(row.repetitions));
    params.set("load", String(row.load));
    params.set("unit", row.unit || "KG");
    if (row.equipment != null) params.set("equipment_id", String(row.equipment));
    if (row.attachment != null) params.set("attachment_id", String(row.attachment));
    if (row.set_type) params.set("set_type", row.set_type);
    if (row.workout_split && row.workout_split !== "None") {
        params.set("workout_split", row.workout_split);
    }
    params.set("return_to", "today");
    return params.toString();
}

function buildPlanLogUrl(target) {
    return "workouts_input.html?" + buildPlanLogQueryParams(target);
}

function formatPlanSetSummary(row, equipmentMap, attachmentMap) {
    var parts = [row.repetitions + " × " + parseFloat(row.load) + " " + row.unit];
    var eqName = dimensionNameFromId(equipmentMap, row.equipment);
    var atName = dimensionNameFromId(attachmentMap, row.attachment);
    if (eqName && eqName !== "None") parts.push(eqName);
    if (atName && atName !== "None") parts.push(atName);
    if (row.set_type && row.set_type !== "Working set") parts.push(row.set_type);
    return parts.join(" · ");
}

function groupPlanRowsByExercise(planRows) {
    var groups = {};
    var order = [];
    planRows.forEach(function (row) {
        var key = row.plan_group_id || "legacy-" + row.workout_split;
        if (!groups[key]) {
            groups[key] = { exercises: {}, exerciseOrder: [] };
            order.push(key);
        }
        var g = groups[key];
        var exId = normalizePlanId(row.exercise);
        if (!g.exercises[exId]) {
            g.exercises[exId] = [];
            g.exerciseOrder.push(exId);
        }
        g.exercises[exId].push(row);
    });
    order.forEach(function (key) {
        var g = groups[key];
        g.exerciseOrder = sortExerciseIdsByPlanSequence(g.exerciseOrder, g.exercises);
        g.exerciseOrder.forEach(function (exId) {
            groups[key].exercises[exId].sort(function (a, b) {
                return a.set_number - b.set_number;
            });
        });
    });
    return order.map(function (key) {
        return groups[key];
    });
}
