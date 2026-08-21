// Today's plan — checklist of planned exercises for the current date.

var exerciseMap = {};
var attachmentMap = {};
var equipmentMap = {};

var TODAY_WORKOUT_TITLE = "Today's workout";

function formatDisplayDate(iso) {
    var d = new Date(iso + "T12:00:00");
    return d.toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" });
}

function statusBadge(loggedCount, plannedCount) {
    if (loggedCount >= plannedCount) {
        return { text: "Done", className: "today-status-badge today-status-badge--done" };
    }
    if (loggedCount > 0) {
        return {
            text: loggedCount + "/" + plannedCount + " logged",
            className: "today-status-badge today-status-badge--partial",
        };
    }
    return { text: "Not started", className: "today-status-badge today-status-badge--pending" };
}

function escapeHtml(text) {
    var div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function renderExerciseRow(exerciseId, sets, actualCounts) {
    var exId = normalizePlanId(exerciseId);
    var exerciseName = dimensionNameFromId(exerciseMap, exId) || "Exercise #" + exId;
    var plannedCount = sets.length;
    var loggedCount = Math.min(actualCounts[exId] || 0, plannedCount);
    var badge = statusBadge(loggedCount, plannedCount);
    var targetSet = sets[loggedCount] || sets[sets.length - 1];
    var logTarget = {
        exerciseId: exId,
        setIndex: loggedCount + 1,
        setRow: targetSet,
        split: targetSet.workout_split,
    };
    var setSummaries = sets
        .map(function (s, idx) {
            return "Set " + (idx + 1) + ": " + formatPlanSetSummary(s, equipmentMap, attachmentMap);
        })
        .join("; ");

    return (
        '<li class="today-exercise-row">' +
        '<div class="today-exercise-header">' +
        "<h3 class=\"today-exercise-name\">" +
        escapeHtml(exerciseName) +
        "</h3>" +
        '<span class="' +
        badge.className +
        '">' +
        escapeHtml(badge.text) +
        "</span>" +
        "</div>" +
        '<p class="today-set-summary">' +
        escapeHtml(setSummaries) +
        "</p>" +
        '<a class="today-log-btn" href="' +
        escapeHtml(buildPlanLogUrl(logTarget)) +
        '">Log this</a>' +
        "</li>"
    );
}

function renderPlanGroups(groups, actualCounts) {
    return groups
        .map(function (group) {
            var exercisesHtml = group.exerciseOrder
                .map(function (exId) {
                    return renderExerciseRow(exId, group.exercises[exId], actualCounts);
                })
                .join("");
            return (
                '<section class="today-plan-card">' +
                "<h2 class=\"today-plan-title\">" +
                escapeHtml(TODAY_WORKOUT_TITLE) +
                "</h2>" +
                '<ul class="today-exercise-list">' +
                exercisesHtml +
                "</ul>" +
                "</section>"
            );
        })
        .join("");
}

function renderEmptyState(nextPlanHint) {
    var nextHtml = nextPlanHint
        ? '<p class="today-empty-next">' + escapeHtml(nextPlanHint) + "</p>"
        : "";
    return (
        '<div class="today-empty">' +
        "<p>Nothing scheduled for today.</p>" +
        nextHtml +
        '<a href="workouts_plan.html" class="cta-button">Plan a workout</a>' +
        "</div>"
    );
}

function loadNextPlanHint(today) {
    var headers = getAuthHeaders();
    if (!headers) return Promise.resolve(null);
    return apiFetch(API_BASE + "/api/plan-series/", { headers: headers })
        .then(function (res) {
            return res.ok ? res.json() : [];
        })
        .then(function (plans) {
            if (!Array.isArray(plans)) return null;
            var upcoming = plans
                .filter(function (p) {
                    return p.next_date && p.next_date > today;
                })
                .sort(function (a, b) {
                    return a.next_date < b.next_date ? -1 : 1;
                });
            if (!upcoming.length) return null;
            var next = upcoming[0];
            return "Next planned: " + next.label + " on " + next.next_date;
        })
        .catch(function () {
            return null;
        });
}

function renderToday(planRows, actualRows) {
    var container = document.getElementById("today_content");
    if (!container) return;

    if (!planRows.length) {
        loadNextPlanHint(planTodayIso()).then(function (hint) {
            container.innerHTML = renderEmptyState(hint);
        });
        return;
    }

    var actualCounts = countActualsByExercise(actualRows);
    var groups = groupPlanRowsByExercise(planRows);
    container.innerHTML = renderPlanGroups(groups, actualCounts);
}

function loadToday() {
    var today = planTodayIso();
    var dateLabel = document.getElementById("today_date_label");
    if (dateLabel) dateLabel.textContent = formatDisplayDate(today);

    var headers = getAuthHeaders();
    if (!headers) {
        showMessage("Please log in to view today's plan.", "error");
        return;
    }

    Promise.all([fetchWorkoutsForDate("plan", today), fetchWorkoutsForDate("actuals", today)]).then(function (
        results
    ) {
        renderToday(results[0], results[1]);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    loadDimensionOptions(
        { exerciseMap: exerciseMap, attachmentMap: attachmentMap, equipmentMap: equipmentMap },
        {
            loginMessage: "Please log in to view today's plan.",
            loadErrorMessage: "Could not load exercise lists.",
        }
    ).then(function () {
        loadToday();
    });
});
