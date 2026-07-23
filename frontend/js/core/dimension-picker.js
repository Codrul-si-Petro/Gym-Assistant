// Shared exercise/attachment/equipment datalist helpers for log + plan pages.
// API_BASE / getAuthHeaders come from api-base.js (load that script first).

var PLACEHOLDER_DIMENSION_ID = -1;

function fillDimensionList(id, items, nameKey, idKey, map) {
    var list = document.getElementById(id);
    var rows = parseDimensionList(items);
    if (list) list.replaceChildren();
    rows.forEach(function (item) {
        if (list) {
            var opt = document.createElement("option");
            opt.value = item[nameKey];
            list.appendChild(opt);
        }
        if (map) map[item[nameKey]] = item[idKey];
    });
}

function parseDimensionList(payload) {
    if (Array.isArray(payload)) return payload;
    if (payload && Array.isArray(payload.results)) return payload.results;
    return [];
}

function dimensionIdFromName(map, name) {
    if (map[name] != null) return map[name];
    if (name === "None") return PLACEHOLDER_DIMENSION_ID;
    return null;
}

function dimensionNameFromId(map, id) {
    var target = normalizeIdForLookup(id);
    for (var name in map) {
        if (normalizeIdForLookup(map[name]) === target) return name;
    }
    return target === PLACEHOLDER_DIMENSION_ID ? "None" : null;
}

function normalizeIdForLookup(value) {
    if (value == null) return null;
    var n = parseInt(value, 10);
    return isFinite(n) ? n : value;
}

/** Build an id→name map from raw dimension rows. */
function buildIdToNameMap(rows, idKey, nameKey) {
    var map = {};
    (rows || []).forEach(function (row) {
        map[row[idKey]] = row[nameKey];
    });
    return map;
}

/**
 * Fetch raw exercise/attachment/equipment lists (shared by log/plan/history).
 * @returns {Promise<{ exercises: Array, attachments: Array, equipment: Array }>}
 */
function fetchDimensionLists(headers) {
    return Promise.all([
        apiFetch(API_BASE + "/api/exercises/", { headers: headers }).then(function (r) {
            return r.ok ? r.json() : [];
        }),
        apiFetch(API_BASE + "/api/attachments/", { headers: headers }).then(function (r) {
            return r.ok ? r.json() : [];
        }),
        apiFetch(API_BASE + "/api/equipment/", { headers: headers }).then(function (r) {
            return r.ok ? r.json() : [];
        }),
    ]).then(function (results) {
        return {
            exercises: parseDimensionList(results[0]),
            attachments: parseDimensionList(results[1]),
            equipment: parseDimensionList(results[2]),
        };
    });
}

/**
 * @param {Object} maps - { exerciseMap, attachmentMap, equipmentMap } mutable name→id maps
 * @param {{ loginMessage?: string, loadErrorMessage?: string }} [options]
 */
function loadDimensionOptions(maps, options) {
    var opts = options || {};
    var headers = getAuthHeaders();
    if (!headers) {
        if (typeof showMessage === "function") {
            showMessage(opts.loginMessage || "Please log in first.", "error");
        }
        return Promise.resolve();
    }

    return fetchDimensionLists(headers)
        .then(function (lists) {
            fillDimensionList(
                "exercises_list",
                lists.exercises,
                "exercise_name",
                "exercise_id",
                maps.exerciseMap
            );
            fillDimensionList(
                "attachments_list",
                lists.attachments,
                "attachment_name",
                "attachment_id",
                maps.attachmentMap
            );
            fillDimensionList(
                "equipment_list",
                lists.equipment,
                "equipment_name",
                "equipment_id",
                maps.equipmentMap
            );
            return lists;
        })
        .catch(function () {
            if (typeof showMessage === "function") {
                showMessage(opts.loadErrorMessage || "Could not load exercise lists.", "error");
            }
        });
}
