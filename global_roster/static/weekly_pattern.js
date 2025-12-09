(function () {
  const grid = document.querySelector(".weekly-pattern-grid");
  const saveBtn = document.getElementById("wp-save-btn");
  if (!grid || !saveBtn) return;

  const traderId = parseInt(grid.dataset.traderId, 10);

  const STATES = ["indifferent", "preferred_shift", "preferred_not_work", "absolute_no"];

  const nextState = (state) => {
    const idx = STATES.indexOf(state);
    if (idx === -1) return "indifferent";
    return STATES[(idx + 1) % STATES.length];
  };

  const updateCellAppearance = (btn, state) => {
    btn.dataset.state = state;
    btn.classList.remove(
      "wp-indifferent",
      "wp-preferred_shift",
      "wp-preferred_not_work",
      "wp-absolute_no"
    );
    btn.classList.add("wp-" + state);
    btn.textContent = state === "indifferent" ? "" : "X";
  };

  grid.addEventListener("click", (e) => {
    const btn = e.target.closest(".wp-cell");
    if (!btn) return;

    const current = btn.dataset.state || "indifferent";
    const next = nextState(current);
    updateCellAppearance(btn, next);
  });

  const collectCells = () => {
    const cells = [];
    grid.querySelectorAll(".wp-cell").forEach((btn) => {
      const day = parseInt(btn.dataset.day, 10);
      const shift = btn.dataset.shift;
      const state = btn.dataset.state || "indifferent";

      let hard_block = false;
      let weight = 0;

      if (state === "preferred_shift") {
        hard_block = false;
        weight = 1;
      } else if (state === "preferred_not_work") {
        hard_block = false;
        weight = -1;
      } else if (state === "absolute_no") {
        hard_block = true;
        weight = 0;
      } else {
        hard_block = false;
        weight = 0;
      }

      cells.push({
        day_of_week: day,
        shift_type: shift,
        hard_block,
        weight,
      });
    });
    return cells;
  };

  const getDaysOffPreference = () => {
    const checked = document.querySelector(
      'input[name="days_off_preference"]:checked'
    );
    return checked ? checked.value : "NONE";
  };

  saveBtn.addEventListener("click", async () => {
    const cells = collectCells();
    const daysOffPreference = getDaysOffPreference();

    const payload = {
      trader_id: traderId,
      cells,
      days_off_preference: daysOffPreference,
    };

    const res = await fetch(`/traders/${traderId}/weekly-pattern`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      alert("Failed to save weekly pattern");
    } else {
      alert("Weekly pattern saved successfully");
    }
  });
})();





