(function () {
  let modalBackdrop, modal, closeBtn, gridBody, saveBtn, resetBtn;
  let currentTraderId = null;
  let currentTraderName = null;

  // Constants (needed by the exported function)
  const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const DAY_CODES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];
  const SHIFT_TYPES = ["FULL", "EARLY", "LATE"]; // Day (FULL), Early, Late

  // Sports list (from hidden element on page)
  const sportsDataEl = document.getElementById("sports-data");
  const ALL_SPORTS = sportsDataEl ? JSON.parse(sportsDataEl.dataset.sports || "[]") : [];

  function dayCodeToIndex(code) {
    return DAY_CODES.indexOf(code);
  }

  function dayIndexToCode(idx) {
    return DAY_CODES[idx] || "";
  }

  // Initialize DOM elements
  function initElements() {
    modalBackdrop = document.getElementById("weekly-pattern-modal-backdrop");
    modal = document.getElementById("weekly-pattern-modal");
    closeBtn = document.getElementById("weekly-pattern-modal-close");
    gridBody = document.getElementById("wp-modal-grid-body");
    saveBtn = document.getElementById("wp-modal-save-btn");
    resetBtn = document.getElementById("wp-modal-reset-btn");
    return modalBackdrop && modal && gridBody && saveBtn;
  }

  let cancelBtn;

  function updateModalTitle() {
    const nameEl = document.getElementById("weekly-pattern-modal-title");
    if (!nameEl || !currentTraderName) return;
    nameEl.textContent = `${currentTraderName} - Preferences`;
  }

  // Load pattern data
  async function loadPatternData() {
    if (!currentTraderId) {
      console.error("No trader ID set");
      return;
    }

    try {
      const url = `/api/traders/${currentTraderId}/weekly-pattern`;
      console.log("Fetching weekly pattern from:", url);
      
      // Add timeout to prevent hanging
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Failed to fetch weekly pattern", response.status, errorText);
        alert(`Failed to load weekly pattern: ${response.status}`);
        return;
      }

      const data = await response.json();
      
      if (!data || !data.cells) {
        console.error("Invalid response data:", data);
        alert("Invalid data received from server");
        return;
      }

      // Day-sport preferences map
      const daySportMap = {};
      (data.day_sport_preferences || []).forEach((item) => {
        const idx = dayCodeToIndex(item.day_of_week);
        if (idx >= 0) {
          daySportMap[idx] = item.sport_code || "";
        }
      });

      // Build grid from data
      const days = [];
      for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
        const shifts = [];
        for (const shiftType of SHIFT_TYPES) {
          const cell = data.cells.find(
            (c) => c.day_of_week === dayIndex && c.shift_type === shiftType
          );
          
          let state = "indifferent";
          if (cell) {
            if (cell.hard_block) {
              state = "absolute_no";
            } else if (cell.weight > 0) {
              state = "preferred_shift";
            } else if (cell.weight < 0) {
              state = "preferred_not_work";
            }
          }

          shifts.push({
            type: shiftType,
            state: state,
          });
        }
        days.push({
          index: dayIndex,
          label: DAY_LABELS[dayIndex],
          shifts: shifts,
          sport_code: daySportMap[dayIndex] || "",
        });
      }

      buildGrid(days);

      // Set days-off preference
      const daysOffPref = data.days_off_preference || "NONE";
      const select = document.getElementById("wp-days-off-dropdown");
      if (select) {
        select.value = daysOffPref;
      }
    } catch (err) {
      console.error("Error fetching weekly pattern", err);
      if (err.name === 'AbortError') {
        alert("Request timed out. Please try again.");
      } else {
        alert(`Failed to load weekly pattern: ${err.message}`);
      }
    }
  }

  // Export function FIRST (before any initialization checks)
  window.openWeeklyPatternModal = async function (traderId, traderName, bioData) {
    console.log("openWeeklyPatternModal called", { traderId, traderName });
    
    // Ensure elements are initialized
    if (!initElements()) {
      console.error("Weekly pattern modal elements not found", {
        backdrop: !!document.getElementById("weekly-pattern-modal-backdrop"),
        modal: !!document.getElementById("weekly-pattern-modal"),
        gridBody: !!document.getElementById("wp-modal-grid-body"),
        saveBtn: !!document.getElementById("wp-modal-save-btn")
      });
      alert("Weekly pattern modal is not available. Please refresh the page.");
      return;
    }

    currentTraderId = traderId;
    currentTraderName = traderName;

    updateModalTitle();

    // Show modal first, then load data
    console.log("Showing modal");
    if (modalBackdrop) modalBackdrop.removeAttribute("hidden");
    if (modal) modal.removeAttribute("hidden");
    document.body.style.overflow = "hidden"; // Disable body scroll

    // Load data asynchronously (don't await - let it load in background)
    console.log("Starting to load pattern data");
    loadPatternData().catch(err => {
      console.error("Error loading pattern data:", err);
      // Show empty grid if load fails
      const emptyDays = [];
      for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
        emptyDays.push({
          index: dayIndex,
          label: DAY_LABELS[dayIndex],
          shifts: SHIFT_TYPES.map(type => ({ type, state: "indifferent" })),
          sport_code: "",
        });
      }
      buildGrid(emptyDays);
    });
  };

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      if (!initElements()) {
        console.error("Weekly pattern modal elements not found on DOMContentLoaded");
      }
    });
  } else {
    if (!initElements()) {
      console.error("Weekly pattern modal elements not found on initial load");
    }
  }

  const DROPDOWN_OPTIONS = [
    { value: "indifferent", label: "", symbol: "" },
    { value: "preferred_shift", label: "Preferred Shift", symbol: "✓" },
    { value: "preferred_not_work", label: "Prefer Not To Work", symbol: "O" },
    { value: "absolute_no", label: "Day OFF", symbol: "X" }
  ];
  
  // Function to update select display to show symbol when selected
  function updateSelectDisplay(select) {
    const selectedValue = select.value;
    const selectedOption = DROPDOWN_OPTIONS.find(opt => opt.value === selectedValue);
    
    // Remove all state classes
    select.classList.remove("wp-preferred_shift", "wp-preferred_not_work", "wp-absolute_no");
    
    if (selectedOption && selectedOption.symbol) {
      // Add state class for styling
      select.classList.add(`wp-${selectedOption.value}`);
      // Store the symbol for display
      select.dataset.displaySymbol = selectedOption.symbol;
    } else {
      select.dataset.displaySymbol = "";
    }
    
    // Update the selected option's text to show symbol
    Array.from(select.options).forEach(opt => {
      if (opt.selected && selectedOption && selectedOption.symbol) {
        // When selected, show only symbol
        opt.textContent = selectedOption.symbol;
      } else if (opt.value === "indifferent") {
        opt.textContent = "";
      } else {
        // When not selected, show full label
        const optData = DROPDOWN_OPTIONS.find(o => o.value === opt.value);
        opt.textContent = optData ? optData.label : "";
      }
    });
  }


  function buildGrid(days) {
    if (!gridBody) return;
    gridBody.innerHTML = "";
    
    days.forEach((day) => {
      const row = document.createElement("tr");
      
      // Add blue background for Sat/Sun
      if (day.index === 5 || day.index === 6) {
        row.classList.add("wp-weekend-row");
      }
      
      const dayCell = document.createElement("td");
      dayCell.textContent = day.label;
      dayCell.className = "wp-day-label";
      dayCell.dataset.day = day.index;
      row.appendChild(dayCell);

      // Sport preference cell
      const sportCell = document.createElement("td");
      const sportSelect = document.createElement("select");
      sportSelect.className = "pref-sport-select wp-cell-select";
      sportSelect.dataset.day = day.index;

      const anyOpt = document.createElement("option");
      anyOpt.value = "";
      anyOpt.textContent = "";
      sportSelect.appendChild(anyOpt);

      ALL_SPORTS.forEach((sport) => {
        const opt = document.createElement("option");
        opt.value = sport.code;
        opt.textContent = sport.code;
        if (day.sport_code && day.sport_code === sport.code) {
          opt.selected = true;
        }
        sportSelect.appendChild(opt);
      });

      sportCell.appendChild(sportSelect);
      row.appendChild(sportCell);

      day.shifts.forEach((shift) => {
        const cell = document.createElement("td");
        
        // Add border class for Day columns (FULL shift)
        if (shift.type === "FULL") {
          cell.classList.add("wp-day-column");
        }
        
        const select = document.createElement("select");
        select.className = "wp-cell-select";
        select.dataset.day = day.index;
        select.dataset.shift = shift.type;
        
        // Add options with full labels
        DROPDOWN_OPTIONS.forEach(option => {
          const opt = document.createElement("option");
          opt.value = option.value;
          // Store both label and symbol
          opt.textContent = option.label || "";
          opt.dataset.symbol = option.symbol || "";
          if (shift.state === option.value) {
            opt.selected = true;
          }
          select.appendChild(opt);
        });
        
        // Set initial display
        updateSelectDisplay(select);
        
        // Update display when selection changes
        select.addEventListener("change", function() {
          // Update this select's display
          updateSelectDisplay(this);
          
          // Reset all other selects in the same row
          row.querySelectorAll(".wp-cell-select").forEach(sel => {
            if (sel !== this) {
              sel.value = "indifferent";
              updateSelectDisplay(sel);
            }
          });
        });
        
        // Also update on focus to ensure correct display
        select.addEventListener("focus", function() {
          // Show full labels when opening dropdown
          Array.from(this.options).forEach(opt => {
            const optData = DROPDOWN_OPTIONS.find(o => o.value === opt.value);
            if (optData) {
              opt.textContent = optData.label || "";
            }
          });
        });
        
        // Update display when closing dropdown
        select.addEventListener("blur", function() {
          updateSelectDisplay(this);
        });
        
        cell.appendChild(select);
        row.appendChild(cell);
      });

      gridBody.appendChild(row);
    });
  }

  function collectCells() {
    const cells = [];
    if (!gridBody) return cells;
    
    const selects = Array.from(gridBody.querySelectorAll(".wp-cell-select"));
    
    selects.forEach((select) => {
      const day = parseInt(select.dataset.day, 10);
      const shift = select.dataset.shift;
      const state = select.value || "indifferent";

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
  }

  function collectDaySportPreferences() {
    const prefs = [];
    if (!gridBody) return prefs;

    const rows = Array.from(gridBody.querySelectorAll("tr"));
    rows.forEach((row) => {
      const day = parseInt(row.querySelector(".wp-day-label")?.dataset?.day || row.dataset.day || "", 10);
      const sportSelect = row.querySelector(".pref-sport-select");
      if (Number.isNaN(day) || !sportSelect) return;
      const code = sportSelect.value || null;
      prefs.push({
        day_of_week: dayIndexToCode(day),
        sport_code: code,
      });
    });

    return prefs;
  }

  function getDaysOffPreference() {
    const select = document.getElementById("wp-days-off-dropdown");
    return select ? select.value : "NONE";
  }

  function closeModal() {
    if (!modalBackdrop || !modal) return;
    modalBackdrop.setAttribute("hidden", "hidden");
    modal.setAttribute("hidden", "hidden");
    document.body.style.overflow = ""; // Re-enable body scroll
  }

  // Reset button handler
  function resetAllSelections() {
    // Reset all dropdowns to indifferent (blank) - use direct querySelector to ensure we find them
    const allSelects = document.querySelectorAll("#wp-modal-grid-body .wp-cell-select");
    allSelects.forEach(select => {
      select.value = "indifferent";
      updateSelectDisplay(select);
    });
    
    // Reset sport dropdowns
    const sportSelects = document.querySelectorAll("#wp-modal-grid-body .pref-sport-select");
    sportSelects.forEach((sel) => {
      sel.value = "";
    });

    // Reset days-off preference to "No Preference"
    const daysOffSelect = document.getElementById("wp-days-off-dropdown");
    if (daysOffSelect) {
      daysOffSelect.value = "NONE";
    }
  }

  // Save button handler
  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const cells = collectCells();
      const daysOffPreference = getDaysOffPreference();
      const daySportPreferences = collectDaySportPreferences();

      const payload = {
        trader_id: currentTraderId,
        cells,
        days_off_preference: daysOffPreference,
        day_sport_preferences: daySportPreferences,
      };

      try {
        const res = await fetch(`/api/traders/${currentTraderId}/weekly-pattern`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          alert("Failed to save weekly pattern");
          return;
        }

        // Success - reload data to reflect changes
        await loadPatternData();
      } catch (err) {
        console.error("Error saving weekly pattern", err);
        alert("Failed to save weekly pattern");
      }
    });
  }

  // Setup event listeners
  function setupEventListeners() {
    // Re-get closeBtn in case it wasn't initialized
    if (!closeBtn) {
      closeBtn = document.getElementById("weekly-pattern-modal-close");
    }
    
    // Close button handler
    if (closeBtn) {
      closeBtn.addEventListener("click", closeModal);
    }

    // Cancel button handler
    cancelBtn = document.getElementById("wp-modal-cancel-btn");
    if (cancelBtn) {
      cancelBtn.addEventListener("click", closeModal);
    }

    // Re-get modalBackdrop in case it wasn't initialized
    if (!modalBackdrop) {
      modalBackdrop = document.getElementById("weekly-pattern-modal-backdrop");
    }

    // Close on backdrop click
    if (modalBackdrop) {
      modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) {
          closeModal();
        }
      });
    }

    // Setup reset button
    const resetBtnEl = document.getElementById("wp-modal-reset-btn");
    if (resetBtnEl) {
      // Remove any existing listeners by cloning
      const newResetBtn = resetBtnEl.cloneNode(true);
      resetBtnEl.parentNode.replaceChild(newResetBtn, resetBtnEl);
      
      newResetBtn.addEventListener("click", () => {
        resetAllSelections();
      });
    }
  }

  // Setup event listeners after initialization
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setupEventListeners();
    });
  } else {
    setupEventListeners();
  }

  // Close on Escape key (global, doesn't need element)
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (modal && !modal.hasAttribute("hidden")) {
        closeModal();
      }
    }
  });

  // Ensure modal is hidden on page load (after elements are initialized)
  function ensureModalHidden() {
    if (modalBackdrop) modalBackdrop.setAttribute("hidden", "hidden");
    if (modal) modal.setAttribute("hidden", "hidden");
  }
  
  // Try to initialize and hide on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureModalHidden);
  } else {
    ensureModalHidden();
  }

})();
