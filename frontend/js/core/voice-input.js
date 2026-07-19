/*
 * Workout voice input — Web Speech API full-screen recording overlay.
 *
 * Listens continuously (across pauses) so users have time to say the exercise,
 * equipment, attachment, reps, and load in one breath without being cut off.
 * The user controls when to stop via the overlay's "Stop recording" button (or
 * Escape); a safety timeout auto-stops after MAX_LISTEN_MS as a last resort.
 *
 * IMPORTANT: SpeechRecognition.stop() is asynchronous in real browsers — the
 * "onend"/final "onresult" events fire later, not synchronously. Any code path
 * that stops listening must NOT clear `activeRecognition` before that happens,
 * or the eventual onend callback's identity check will (correctly) ignore it
 * and the transcript will never be applied to the form. requestStop() below
 * only asks the recognizer to stop; onend still owns clearing state + finalizing.
 *
 * Usage (plain script, exposes window.GymVoiceInput):
 *   GymVoiceInput.init({
 *     getMaps: function () { return { exerciseMap, equipmentMap, attachmentMap }; },
 *     onParsed: function (parsed) { ... fill form fields ... },
 *     showError: function (message) { ... },
 *   });
 */
(function () {
    /** Safety auto-stop so a session can't run forever (e.g. mic left on by accident). */
    var MAX_LISTEN_MS = 45000;
    /** If the recognizer never fires onend after stop() (flaky browser), finalize anyway. */
    var STOP_FALLBACK_MS = 4000;

    var activeRecognition = null;
    var config = null;
    var listenStartedAt = null;
    var finalTranscript = "";
    var interimTranscript = "";
    var gotAnyResult = false;
    var isStopping = false;

    var maxDurationTimer = null;
    var countdownInterval = null;
    var stopFallbackTimer = null;

    function getSpeechRecognitionConstructor() {
        return window.SpeechRecognition || window.webkitSpeechRecognition || null;
    }

    function splitWords(text) {
        return (text || "").trim().split(/\s+/).filter(Boolean);
    }

    function cancelMaxDurationTimer() {
        if (maxDurationTimer !== null) {
            clearTimeout(maxDurationTimer);
            maxDurationTimer = null;
        }
    }

    function cancelCountdown() {
        if (countdownInterval !== null) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }
    }

    function cancelStopFallback() {
        if (stopFallbackTimer !== null) {
            clearTimeout(stopFallbackTimer);
            stopFallbackTimer = null;
        }
    }

    function overlayEls() {
        return {
            overlay: document.getElementById("voice-overlay"),
            transcript: document.getElementById("voice-overlay-transcript"),
            timer: document.getElementById("voice-overlay-timer"),
            stopBtn: document.getElementById("voice-overlay-stop"),
        };
    }

    function setStopButtonBusy(busy) {
        var stopBtn = overlayEls().stopBtn;
        if (!stopBtn) return;
        stopBtn.disabled = !!busy;
        stopBtn.textContent = busy ? "Finishing…" : "Stop recording";
    }

    function showOverlay() {
        var overlay = overlayEls().overlay;
        if (!overlay) return;
        overlay.hidden = false;
        document.body.style.overflow = "hidden";
    }

    function hideOverlay() {
        var overlay = overlayEls().overlay;
        if (!overlay) return;
        overlay.hidden = true;
        document.body.style.overflow = "";
    }

    function renderLiveTranscript() {
        var transcriptEl = overlayEls().transcript;
        if (!transcriptEl) return;
        transcriptEl.innerHTML = "";

        splitWords(finalTranscript).forEach(function (word) {
            var chip = document.createElement("span");
            chip.className = "voice-word-chip voice-word-chip--final";
            chip.textContent = word;
            transcriptEl.appendChild(chip);
        });
        splitWords(interimTranscript).forEach(function (word) {
            var chip = document.createElement("span");
            chip.className = "voice-word-chip voice-word-chip--interim";
            chip.textContent = word;
            transcriptEl.appendChild(chip);
        });

        if (!transcriptEl.children.length) {
            var placeholder = document.createElement("span");
            placeholder.className = "voice-live-placeholder";
            placeholder.textContent = "Listening for exercise, equipment, attachment, reps, load…";
            transcriptEl.appendChild(placeholder);
        }
    }

    function setStatus(text, listening) {
        var status = document.getElementById("voice-status");
        if (!status) return;
        if (!text) {
            status.textContent = "";
            status.hidden = true;
            status.classList.remove("voice-status--listening");
            return;
        }
        status.textContent = text;
        status.hidden = false;
        status.classList.toggle("voice-status--listening", !!listening);
    }

    function updateTimer() {
        var timerEl = overlayEls().timer;
        if (!timerEl || listenStartedAt == null) return;
        var elapsedMs = Date.now() - listenStartedAt;
        var remainingSec = Math.max(0, Math.ceil((MAX_LISTEN_MS - elapsedMs) / 1000));
        timerEl.textContent = remainingSec + "s left";
    }

    function setMicListening(listening) {
        var micBtn = document.getElementById("mic-btn");
        if (!micBtn) return;
        micBtn.classList.toggle("mic-btn--listening", !!listening);
        micBtn.setAttribute("aria-pressed", listening ? "true" : "false");
        micBtn.setAttribute("aria-label", listening ? "Stop dictation" : "Dictate workout");
    }

    function resetListeningState() {
        cancelMaxDurationTimer();
        cancelCountdown();
        cancelStopFallback();
        listenStartedAt = null;
        finalTranscript = "";
        interimTranscript = "";
        gotAnyResult = false;
        isStopping = false;
    }

    /** Hard-discard any in-flight session (e.g. right before starting a new one). No finalize. */
    function discardActiveRecognition() {
        if (activeRecognition) {
            var rec = activeRecognition;
            activeRecognition = null;
            try {
                if (rec.abort) rec.abort();
                else rec.stop();
            } catch (e) {}
        }
        cancelMaxDurationTimer();
        cancelCountdown();
        cancelStopFallback();
    }

    function handleError(errorCode) {
        var messages = {
            "not-allowed": "Microphone access denied. Allow the mic in browser settings.",
            "service-not-allowed": "Speech recognition is not allowed in this browser context.",
            "no-speech": "No speech detected. Tap the mic and try again.",
            "audio-capture": "No microphone found.",
            network: "Voice input needs a network connection.",
            aborted: "Voice input cancelled.",
        };
        var message = messages[errorCode] || "Could not recognize speech. Try again.";
        setStatus(message, false);
        if (config && config.showError) config.showError(message);
    }

    /** Parse and apply whatever transcript was captured, then reset for next time. */
    function finishSession() {
        hideOverlay();
        setStopButtonBusy(false);
        setMicListening(false);

        var transcript = (finalTranscript + " " + interimTranscript).trim();

        if (!transcript) {
            setStatus(
                gotAnyResult
                    ? "Could not make out any words. Tap the mic and try again."
                    : "No speech detected. Tap the mic and try again.",
                false
            );
            resetListeningState();
            return;
        }

        var maps = config.getMaps ? config.getMaps() : {};
        var parsed = window.GymVoiceTranscriptParser.parse(transcript, maps);
        if (config.onParsed) config.onParsed(parsed);
        setStatus(
            "Heard: " + window.GymVoiceTranscriptParser.formatSummary(parsed) + " — review and submit.",
            false
        );
        resetListeningState();
    }

    /** User-initiated (or timeout-initiated) graceful stop. Does not clear state itself. */
    function requestStop() {
        if (!activeRecognition || isStopping) return;
        isStopping = true;
        setMicListening(false);
        setStopButtonBusy(true);
        setStatus("Finishing up…", true);

        var rec = activeRecognition;
        try {
            rec.stop();
        } catch (e) {}

        // Some environments (and browser implementations) fire onend synchronously —
        // if that already ran and finalized, there's nothing left to schedule.
        if (activeRecognition !== rec) return;

        cancelMaxDurationTimer();
        cancelCountdown();
        cancelStopFallback();
        stopFallbackTimer = setTimeout(function () {
            stopFallbackTimer = null;
            if (activeRecognition === rec) {
                activeRecognition = null;
                try {
                    if (rec.abort) rec.abort();
                } catch (e) {}
                finishSession();
            }
        }, STOP_FALLBACK_MS);
    }

    function startRecognition() {
        var SpeechRecognition = getSpeechRecognitionConstructor();
        if (!SpeechRecognition || !config) return;

        discardActiveRecognition();
        resetListeningState();
        setStatus("Listening…", true);
        setMicListening(true);
        setStopButtonBusy(false);
        showOverlay();
        renderLiveTranscript();
        listenStartedAt = Date.now();
        updateTimer();
        countdownInterval = setInterval(updateTimer, 1000);

        var recognition = new SpeechRecognition();
        activeRecognition = recognition;
        recognition.lang = "en-US";
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        recognition.onresult = function (event) {
            if (activeRecognition !== recognition) return;
            gotAnyResult = true;
            interimTranscript = "";
            for (var i = event.resultIndex; i < event.results.length; i++) {
                var result = event.results[i];
                var text = (result[0] && result[0].transcript) || "";
                if (result.isFinal) {
                    finalTranscript = (finalTranscript + " " + text).trim();
                } else {
                    interimTranscript = (interimTranscript + " " + text).trim();
                }
            }
            renderLiveTranscript();
        };

        recognition.onerror = function (event) {
            if (activeRecognition !== recognition) return;
            // "no-speech" while continuous just means silence so far — keep listening.
            if (event.error === "no-speech") return;
            activeRecognition = null;
            handleError(event.error);
            hideOverlay();
            setMicListening(false);
            resetListeningState();
        };

        recognition.onend = function () {
            if (activeRecognition !== recognition) return;
            activeRecognition = null;
            cancelStopFallback();
            finishSession();
        };

        maxDurationTimer = setTimeout(function () {
            maxDurationTimer = null;
            requestStop();
        }, MAX_LISTEN_MS);

        try {
            recognition.start();
        } catch (e) {
            activeRecognition = null;
            hideOverlay();
            setMicListening(false);
            resetListeningState();
            var message = "Could not start voice input. Try again.";
            setStatus(message, false);
            if (config.showError) config.showError(message);
        }
    }

    function init(options) {
        config = options || {};
        var micBtn = document.getElementById("mic-btn");
        if (!micBtn) return;

        if (!getSpeechRecognitionConstructor()) {
            micBtn.hidden = true;
            return;
        }

        micBtn.hidden = false;
        micBtn.addEventListener("click", function () {
            if (activeRecognition) {
                requestStop();
                return;
            }
            startRecognition();
        });

        var stopBtn = overlayEls().stopBtn;
        if (stopBtn) stopBtn.addEventListener("click", requestStop);

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && activeRecognition) requestStop();
        });
    }

    window.GymVoiceInput = { init: init };
})();
