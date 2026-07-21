// Shared exercise/attachment/equipment datalist helpers for log + plan pages.

if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === "::1"
) {
    API_BASE = "http://127.0.0.1:8000";
} else {
    API_BASE = "https://api.gym-assistant.app";
}

var PLACEHOLDER_DIMENSION_ID = -1;

function getAuthHeaders() {
    var token = localStorage.getItem("access_token");
    if (!token) return null;
    return {
        Authorization: "Bearer " + token,
        Accept: "application/json",
        "Content-Type": "application/json",
    };
}

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

    return Promise.all([
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
            fillDimensionList("exercises_list", results[0], "exercise_name", "exercise_id", maps.exerciseMap);
            fillDimensionList("attachments_list", results[1], "attachment_name", "attachment_id", maps.attachmentMap);
            fillDimensionList("equipment_list", results[2], "equipment_name", "equipment_id", maps.equipmentMap);
        })
        .catch(function () {
            if (typeof showMessage === "function") {
                showMessage(opts.loadErrorMessage || "Could not load exercise lists.", "error");
            }
        });
}
