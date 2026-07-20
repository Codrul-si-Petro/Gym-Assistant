/*
 * Workout voice transcript parser — turns speech-to-text output into structured fields.
 * Relies on the browser transcribing numbers as digits (e.g. "10 reps").
 *
 * Usage (plain script, exposes window.GymVoiceTranscriptParser):
 *   var parsed = GymVoiceTranscriptParser.parse(transcript, {
 *     exerciseMap, equipmentMap, attachmentMap
 *   });
 */
(function () {
    var DEFAULT_MATCH_THRESHOLD = 0.35;

    function normalizeVoiceText(text) {
        return (text || "")
            .toLowerCase()
            .replace(/[^\w\s]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    }

    function tokenizeVoiceText(text) {
        return normalizeVoiceText(text).split(" ").filter(Boolean);
    }

    function escapeRegExp(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function removeWordsFromText(text, words) {
        var result = text;
        (words || []).forEach(function (word) {
            result = result.replace(new RegExp("\\b" + escapeRegExp(word) + "\\b", "gi"), " ");
        });
        return result.replace(/\s+/g, " ").trim();
    }

    function titleCaseWords(text) {
        return (text || "")
            .split(" ")
            .filter(Boolean)
            .map(function (word) {
                return word.charAt(0).toUpperCase() + word.slice(1);
            })
            .join(" ");
    }

    /**
     * Score phrase against map keys using word overlap (Jaccard + coverage).
     * @returns {{ name: string, score: number } | null}
     */
    function matchAgainstMap(phrase, map, threshold) {
        var minScore = threshold != null ? threshold : DEFAULT_MATCH_THRESHOLD;
        var phraseTokens = tokenizeVoiceText(phrase);
        if (!phraseTokens.length) return null;

        var bestName = null;
        var bestScore = 0;

        Object.keys(map || {}).forEach(function (name) {
            var nameTokens = tokenizeVoiceText(name);
            if (!nameTokens.length) return;

            var intersection = 0;
            phraseTokens.forEach(function (token) {
                if (nameTokens.indexOf(token) !== -1) intersection += 1;
            });

            var union = {};
            phraseTokens.concat(nameTokens).forEach(function (token) {
                union[token] = true;
            });
            var unionSize = Object.keys(union).length;
            var jaccard = unionSize ? intersection / unionSize : 0;
            var coverage = nameTokens.length ? intersection / nameTokens.length : 0;
            var score = Math.max(jaccard, coverage * 0.85);

            if (score > bestScore) {
                bestScore = score;
                bestName = name;
            }
        });

        if (bestName && bestScore >= minScore) {
            return { name: bestName, score: bestScore };
        }
        return null;
    }

    /**
     * @param {string} transcript
     * @param {{ exerciseMap?: object, equipmentMap?: object, attachmentMap?: object }} maps
     */
    function parseVoiceTranscript(transcript, maps) {
        var exerciseMap = (maps && maps.exerciseMap) || {};
        var equipmentMap = (maps && maps.equipmentMap) || {};
        var attachmentMap = (maps && maps.attachmentMap) || {};

        var text = normalizeVoiceText(transcript);
        var result = {
            exercise: null,
            exerciseRaw: null,
            equipment: null,
            attachment: null,
            equipmentForceClear: false,
            attachmentForceClear: false,
            repetitions: null,
            load: null,
            unit: null,
        };

        var repsMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:reps?|repetitions?)/);
        if (repsMatch) {
            result.repetitions = parseInt(repsMatch[1], 10);
            text = text.replace(repsMatch[0], " ");
        }

        var loadMatch = text.match(/(\d+(?:\.\d+)?)\s*(kg|kgs|kilograms?|kilos?|lbs?|pounds?)/);
        if (loadMatch) {
            result.load = parseFloat(loadMatch[1]);
            result.unit = /lb|pound/.test(loadMatch[2]) ? "LBS" : "KG";
            text = text.replace(loadMatch[0], " ");
        }

        var nonePatterns = [
            { regex: /\b(?:no|without|none)\s+attachment\b/g, key: "attachmentForceClear" },
            { regex: /\battachment\s+(?:none|not\s+used)\b/g, key: "attachmentForceClear" },
            { regex: /\b(?:no|without|none)\s+equipment\b/g, key: "equipmentForceClear" },
            { regex: /\bequipment\s+(?:none|not\s+used)\b/g, key: "equipmentForceClear" },
        ];
        nonePatterns.forEach(function (pattern) {
            if (pattern.regex.test(text)) {
                result[pattern.key] = true;
                text = text.replace(pattern.regex, " ");
            }
        });

        text = text.replace(/\s+/g, " ").trim();

        if (!result.equipmentForceClear) {
            var equipmentMatch = matchAgainstMap(text, equipmentMap);
            if (equipmentMatch) {
                result.equipment = equipmentMatch.name;
                text = removeWordsFromText(text, tokenizeVoiceText(equipmentMatch.name));
            }
        }

        if (!result.attachmentForceClear) {
            var attachmentMatch = matchAgainstMap(text, attachmentMap);
            if (attachmentMatch) {
                result.attachment = attachmentMatch.name;
                text = removeWordsFromText(text, tokenizeVoiceText(attachmentMatch.name));
            }
        }

        var fillers = [
            "sets of",
            "set of",
            "did",
            "with",
            "using",
            "for",
            "and",
            "at",
            "on",
            "the",
            "a",
            "an",
        ];
        fillers.forEach(function (filler) {
            text = text.replace(new RegExp("\\b" + escapeRegExp(filler) + "\\b", "g"), " ");
        });
        text = text.replace(/\s+/g, " ").trim();

        var exerciseMatch = matchAgainstMap(text, exerciseMap, 0.3);
        if (exerciseMatch) {
            result.exercise = exerciseMatch.name;
        } else if (text) {
            result.exerciseRaw = titleCaseWords(text);
        }

        return result;
    }

    function formatVoiceResultSummary(parsed) {
        var parts = [];
        var exerciseLabel = parsed.exercise || parsed.exerciseRaw || "exercise";
        parts.push(exerciseLabel);

        if (parsed.equipmentForceClear) {
            parts.push("no equipment");
        } else if (parsed.equipment) {
            parts.push(parsed.equipment);
        }

        if (parsed.attachmentForceClear) {
            parts.push("no attachment");
        } else if (parsed.attachment) {
            parts.push(parsed.attachment);
        }

        if (parsed.repetitions != null) {
            parts.push(parsed.repetitions + " reps");
        }
        if (parsed.load != null) {
            parts.push(parsed.load + " " + (parsed.unit === "LBS" ? "lbs" : "kg"));
        }

        return parts.join(" · ");
    }

    window.GymVoiceTranscriptParser = {
        parse: parseVoiceTranscript,
        formatSummary: formatVoiceResultSummary,
    };
})();
