/*
 * Shared edit sheet: a <dialog> that renders as a centered modal on desktop
 * and a bottom sheet on small screens. Pages provide the form body and a
 * save handler; the sheet handles open/close, error display and busy state.
 *
 * Usage (plain script, exposes window.GymEditSheet):
 *   const sheet = GymEditSheet.create({ title: "Edit set" });
 *   sheet.open({ formHtml, onSave: async (formEl) => {...} });
 */
(function () {
  function create(options) {
    const title = (options && options.title) || "Edit";

    const dialog = document.createElement("dialog");
    dialog.className = "edit-sheet";
    dialog.innerHTML = `
      <div class="edit-sheet-surface" role="document">
        <div class="edit-sheet-header">
          <h2 class="edit-sheet-title"></h2>
          <button type="button" class="edit-sheet-close" aria-label="Close">×</button>
        </div>
        <p class="edit-sheet-error" role="alert" aria-live="polite" hidden></p>
        <form class="edit-sheet-form" method="dialog" novalidate>
          <div class="edit-sheet-body"></div>
          <div class="edit-sheet-actions">
            <button type="button" class="edit-sheet-cancel">Cancel</button>
            <button type="submit" class="edit-sheet-save">Save</button>
          </div>
        </form>
      </div>`;
    document.body.appendChild(dialog);

    const titleEl = dialog.querySelector(".edit-sheet-title");
    const errorEl = dialog.querySelector(".edit-sheet-error");
    const bodyEl = dialog.querySelector(".edit-sheet-body");
    const formEl = dialog.querySelector(".edit-sheet-form");
    const saveBtn = dialog.querySelector(".edit-sheet-save");

    titleEl.textContent = title;
    let currentOnSave = null;

    function setError(message) {
      errorEl.textContent = message || "";
      errorEl.hidden = !message;
    }

    function setBusy(busy) {
      saveBtn.disabled = busy;
      saveBtn.textContent = busy ? "Saving…" : "Save";
    }

    function close() {
      if (dialog.open) dialog.close();
    }

    dialog.querySelector(".edit-sheet-close").addEventListener("click", close);
    dialog.querySelector(".edit-sheet-cancel").addEventListener("click", close);

    // close when tapping the backdrop (the dialog element itself)
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) close();
    });

    formEl.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!currentOnSave) return;
      setError("");
      setBusy(true);
      try {
        await currentOnSave(formEl);
        close();
      } catch (err) {
        setError((err && err.message) || "Failed to save changes.");
      } finally {
        setBusy(false);
      }
    });

    return {
      open({ formHtml, onSave, title: openTitle }) {
        if (openTitle) titleEl.textContent = openTitle;
        bodyEl.innerHTML = formHtml;
        currentOnSave = onSave;
        setError("");
        setBusy(false);
        dialog.showModal();
        const firstField = bodyEl.querySelector("input, select, textarea");
        if (firstField) firstField.focus();
      },
      close,
      setError,
      element: dialog,
    };
  }

  window.GymEditSheet = { create };
})();
