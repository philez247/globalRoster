document.addEventListener("DOMContentLoaded", () => {
  const requestTypeSelect = document.getElementById("requestType");
  const form = document.getElementById("request-form");
  
  if (!requestTypeSelect || !form) {
    return;
  }
  
  // Cache form groups
  const groupDateFrom = document.getElementById("group-date-from");
  const groupDateTo = document.getElementById("group-date-to");
  const groupShift = document.getElementById("group-shift");
  const groupSport = document.getElementById("group-sport");
  const groupReason = document.getElementById("group-reason");
  
  // Get input elements for clearing values
  const dateToInput = document.getElementById("date_to");
  const shiftSelect = document.getElementById("shift_type");
  const sportInput = document.getElementById("sport_code");
  
  function show(el) {
    if (el) el.removeAttribute("hidden");
  }
  
  function hide(el) {
    if (el) el.setAttribute("hidden", "hidden");
  }
  
  function updateFormVisibility() {
    const type = requestTypeSelect.value;
    
    // Hide everything first
    hide(groupDateFrom);
    hide(groupDateTo);
    hide(groupShift);
    hide(groupSport);
    hide(groupReason);
    
    if (!type) {
      // Nothing selected – only Request Type remains visible
      return;
    }
    
    // Set required attribute on date_to based on type
    if (dateToInput) {
      if (type === "REQUEST_OFF_RANGE") {
        dateToInput.setAttribute("required", "required");
      } else {
        dateToInput.removeAttribute("required");
      }
    }
    
    if (type === "REQUEST_IN") {
      // Single day, with shift + sport + reason
      show(groupDateFrom);
      show(groupShift);
      show(groupSport);
      show(groupReason);
      // date_to stays hidden
    } else if (type === "REQUEST_OFF_DAY") {
      // Single day off, no sport/shift
      show(groupDateFrom);
      show(groupReason);
    } else if (type === "REQUEST_OFF_RANGE") {
      // Date range off, no sport/shift
      show(groupDateFrom);
      show(groupDateTo);
      show(groupReason);
    }
  }
  
  // Wire up change listener and set initial state
  requestTypeSelect.addEventListener("change", updateFormVisibility);
  updateFormVisibility(); // set initial state when the page loads
  
  // Clean up hidden values on submit
  form.addEventListener("submit", (e) => {
    const type = requestTypeSelect.value;
    
    if (type === "REQUEST_IN" || type === "REQUEST_OFF_DAY") {
      // Clear date_to for single-day requests
      if (dateToInput) {
        dateToInput.value = "";
      }
    }
    
    if (type === "REQUEST_OFF_DAY" || type === "REQUEST_OFF_RANGE") {
      // Clear shift and sport for off-day/range requests
      if (shiftSelect) {
        shiftSelect.value = "";
      }
      if (sportInput) {
        sportInput.value = "";
      }
    }
  });
});

