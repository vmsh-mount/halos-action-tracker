(() => {
  "use strict";

  // Destructive actions ask first. Every submitted form locks its buttons so a second click cannot repeat it.
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) {
      event.preventDefault();
      return;
    }
    if (form.matches("form.composer") && !validateComposer(form)) {
      event.preventDefault();
      return;
    }
    if (form.dataset.sent) {
      event.preventDefault();
      return;
    }
    form.dataset.sent = "1";
    // After this tick, so the pressed button's own value is still sent with the form.
    setTimeout(() => form.querySelectorAll("button").forEach((button) => (button.disabled = true)), 0);
    if (form.matches("form.composer")) showProgress(form);
  });
  // Coming back with the browser's Back button restores the page from cache with the buttons still locked.
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    document.querySelectorAll("form[data-sent]").forEach((form) => {
      delete form.dataset.sent;
      form.querySelectorAll("button").forEach((button) => (button.disabled = false));
      form.querySelectorAll(".progress, .bar").forEach((el) => (el.hidden = true));
    });
  });

  function validateComposer(form) {
    const text = form.querySelector("textarea"), file = form.querySelector("input[type=file]");
    const problem = form.querySelector(".field-error");
    const empty = !text.value.trim() && !(file && file.files.length);
    text.setAttribute("aria-invalid", empty ? "true" : "false");
    problem.hidden = !empty;
    if (empty) text.focus();
    return !empty;
  }

  function showProgress(form) {
    const progress = form.querySelector(".progress"), bar = form.querySelector(".bar");
    if (!progress) return;
    progress.hidden = false;
    if (bar) bar.hidden = false;
    const seconds = progress.querySelector(".seconds"), started = Date.now();
    setInterval(() => (seconds.textContent = `${Math.round((Date.now() - started) / 1000)}s`), 1000);
  }

  for (const form of document.querySelectorAll("form.composer")) {
    const file = form.querySelector("input[type=file]"), date = form.querySelector("input[type=date]");
    const name = form.querySelector(".file-name"), text = form.querySelector("textarea");
    if (file) {
      file.addEventListener("change", () => {
        const chosen = file.files[0];
        name.textContent = chosen ? chosen.name : "";
        const dated = chosen && chosen.name.match(/\d{4}-\d{2}-\d{2}/);
        if (dated) date.value = dated[0];
        if (chosen) validateComposer(form);
      });
    }
    text.addEventListener("input", () => {
      if (text.getAttribute("aria-invalid") === "true") validateComposer(form);
    });
  }

  // Tracked work: filter and sort in the page. Nothing is fetched.
  for (const region of document.querySelectorAll("[data-work]")) {
    const body = region.querySelector("tbody");
    if (!body) continue;
    const rows = [...body.querySelectorAll("tr")], none = region.querySelector(".no-match");
    const owner = region.querySelector("select[data-owner-filter]");
    let filter = "all";

    const matches = (row) => {
      const d = row.dataset;
      const byFilter =
        filter === "all" || (filter === "active" && d.group === "active") || (filter === "closed" && d.group === "closed") ||
        (filter === "blocked" && d.status === "blocked") || (filter === "overdue" && d.overdue === "1") ||
        (filter === "unassigned" && d.group === "active" && !d.owner);
      return byFilter && (!owner || !owner.value || d.owner === owner.value);
    };
    const apply = () => {
      let shown = 0;
      for (const row of rows) {
        row.hidden = !matches(row);
        if (!row.hidden) shown += 1;
      }
      if (none) none.hidden = shown > 0 || rows.length === 0;
    };
    region.querySelectorAll("[data-filter]").forEach((button) =>
      button.addEventListener("click", () => {
        filter = button.dataset.filter;
        region.querySelectorAll("[data-filter]").forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
        apply();
      })
    );
    if (owner) owner.addEventListener("change", apply);

    const statusOrder = ["blocked", "in_progress", "open", "done", "dropped"];
    const keyOf = { id: (r) => Number(r.dataset.n), owner: (r) => r.dataset.owner || "￿", due: (r) => r.dataset.due || "9999", status: (r) => statusOrder.indexOf(r.dataset.status) };
    region.querySelectorAll("th[data-sort]").forEach((head) =>
      head.querySelector("button").addEventListener("click", () => {
        const down = head.getAttribute("aria-sort") === "ascending";
        region.querySelectorAll("th[data-sort]").forEach((h) => h.removeAttribute("aria-sort"));
        head.setAttribute("aria-sort", down ? "descending" : "ascending");
        const key = keyOf[head.dataset.sort], field = head.dataset.sort;
        const blank = (row) => (field === "owner" || field === "due") && !row.dataset[field];
        rows.sort((a, b) => {
          if (blank(a) !== blank(b)) return blank(a) ? 1 : -1; // items with no owner or date stay last either way
          const order = key(a) < key(b) ? -1 : key(a) > key(b) ? 1 : 0;
          return order ? order * (down ? -1 : 1) : Number(a.dataset.n) - Number(b.dataset.n);
        });
        rows.forEach((row) => body.appendChild(row));
      })
    );
  }

  // Only one edit panel open at a time, and Escape closes it.
  const editors = [...document.querySelectorAll("details.edit")];
  editors.forEach((panel) => {
    panel.addEventListener("toggle", () => {
      if (panel.open) editors.forEach((other) => other !== panel && (other.open = false));
    });
    panel.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        panel.open = false;
        panel.querySelector("summary").focus();
      }
    });
  });
})();
