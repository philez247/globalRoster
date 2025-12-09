document.addEventListener("DOMContentLoaded", () => {
  // Add Trader Modal handlers
  const addTraderModal = document.getElementById("addTraderModal");
  const addTraderModalContainer = document.getElementById("addTraderModalContainer");
  const btnAddTrader = document.getElementById("btnAddTrader");
  const btnCloseAddTrader = document.getElementById("btnCloseAddTrader");
  const btnCancelAddTrader = document.getElementById("btnCancelAddTrader");

  function openAddTraderModal() {
    if (addTraderModal) addTraderModal.removeAttribute("hidden");
    if (addTraderModalContainer) addTraderModalContainer.removeAttribute("hidden");
  }

  function closeAddTraderModal() {
    if (addTraderModal) addTraderModal.setAttribute("hidden", "hidden");
    if (addTraderModalContainer) addTraderModalContainer.setAttribute("hidden", "hidden");
  }

  if (btnAddTrader) {
    btnAddTrader.addEventListener("click", openAddTraderModal);
  }

  if (btnCloseAddTrader) {
    btnCloseAddTrader.addEventListener("click", closeAddTraderModal);
  }

  if (btnCancelAddTrader) {
    btnCancelAddTrader.addEventListener("click", closeAddTraderModal);
  }

  if (addTraderModal) {
    addTraderModal.addEventListener("click", (e) => {
      if (e.target === addTraderModal) {
        closeAddTraderModal();
      }
    });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && addTraderModalContainer && !addTraderModalContainer.hasAttribute("hidden")) {
      closeAddTraderModal();
    }
  });

  // Handle Add Trader form submission with AJAX to catch duplicate alias errors
  const addTraderForm = document.querySelector("#addTraderModalContainer form");
  if (addTraderForm) {
    addTraderForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      const formData = new FormData(addTraderForm);
      const submitButton = addTraderForm.querySelector('button[type="submit"]');
      const originalButtonText = submitButton ? submitButton.textContent : "Save trader";
      
      // Disable submit button during request
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Saving...";
      }
      
      try {
        const response = await fetch("/traders", {
          method: "POST",
          body: formData,
        });
        
        if (response.ok) {
          // Success - redirect
          const redirectTo = formData.get("redirect_to") || "/traders";
          window.location.href = redirectTo;
        } else {
          // Error - check if it's a duplicate alias
          let errorMessage = "Failed to create trader. Please try again.";
          try {
            // Read response as text first (can only read once)
            const text = await response.text();
            if (text) {
              try {
                const errorData = JSON.parse(text);
                if (errorData.detail) {
                  errorMessage = errorData.detail;
                }
              } catch (e2) {
                // Not JSON, use text as error message
                errorMessage = text || errorMessage;
              }
            }
          } catch (e) {
            // Use default message if reading fails
            console.error("Error reading response:", e);
          }
          
          // Check if it's a duplicate alias error
          const lowerMessage = errorMessage.toLowerCase();
          if (lowerMessage.includes("alias") && 
              (lowerMessage.includes("already") || 
               lowerMessage.includes("exists"))) {
            // Show warning popup for duplicate alias
            alert("Alias already exists. Please choose a different alias.");
            // Focus on alias field so user can change it
            const aliasInput = document.getElementById("modal-alias");
            if (aliasInput) {
              aliasInput.focus();
              aliasInput.select();
            }
          } else {
            // Other error - show alert
            alert(errorMessage);
          }
        }
      } catch (error) {
        console.error("Error submitting form:", error);
        alert("An error occurred while creating the trader. Please try again.");
      } finally {
        // Re-enable submit button
        if (submitButton) {
          submitButton.disabled = false;
          submitButton.textContent = originalButtonText;
        }
      }
    });
  }

  // Location and Sport dropdown handlers (for both modal and regular form)
  const locationSelects = [
    document.getElementById("location"),
    document.getElementById("modal-location")
  ].filter(Boolean);
  
  const primarySportSelects = [
    document.getElementById("primary_sport"),
    document.getElementById("modal-primary_sport")
  ].filter(Boolean);
  
  const secondarySportSelects = [
    document.getElementById("secondary_sport"),
    document.getElementById("modal-secondary_sport")
  ].filter(Boolean);

  // Track previous values for location selects to enable revert on cancel/error
  const locationPreviousValues = new Map();
  locationSelects.forEach((select) => {
    if (select) {
      locationPreviousValues.set(select, select.value || "");
    }
  });

  async function handleAddLocation(selectElement) {
    const lastValue = locationPreviousValues.get(selectElement) || "";
    
    // Show single prompt for location code
    const codeInput = window.prompt("Enter location code (e.g., DUB):");
    
    // Handle cancel or empty input
    if (codeInput === null || !codeInput.trim()) {
      selectElement.value = lastValue;
      return;
    }
    
    // Trim and validate
    const code = codeInput.trim().toUpperCase();
    
    // Validate: length and no spaces
    if (code.length > 15) {
      alert("Location code must be <= 15 characters, no spaces");
      selectElement.value = lastValue;
      return;
    }
    
    if (code.includes(" ")) {
      alert("Location code must be <= 15 characters, no spaces");
      selectElement.value = lastValue;
      return;
    }
    
    if (code.length === 0) {
      selectElement.value = lastValue;
      return;
    }
    
    try {
      // Call backend with JSON
      const response = await fetch("/config/locations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      });
      
      if (!response.ok) {
        // Try to parse error message
        let errorMessage = "Could not add location";
        try {
          const errorData = await response.json();
          // Handle FastAPI validation errors (422) and HTTPException (400)
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              // Pydantic validation errors come as array
              const firstError = errorData.detail[0];
              errorMessage = firstError?.msg || "Invalid location code";
            } else {
              // HTTPException detail is a string
              errorMessage = errorData.detail;
            }
          }
        } catch (e) {
          // Use default message if parsing fails
        }
        alert(errorMessage);
        selectElement.value = lastValue;
        return;
      }
      
      const data = await response.json();
      
      // Find the "+ Add location…" option
      const addOption = selectElement.querySelector(
        'option[value="__add_location__"]'
      );
      if (addOption) {
        // Create new option and insert before "Add location"
        const newOption = document.createElement("option");
        newOption.value = data.code;
        newOption.textContent = data.code;
        selectElement.insertBefore(newOption, addOption);
        selectElement.value = data.code;
        // Update previous value
        locationPreviousValues.set(selectElement, data.code);
      }
    } catch (error) {
      console.error("Error creating location:", error);
      alert("Failed to create location. Please try again.");
      selectElement.value = lastValue;
    }
  }

  function handleAddSport(selectElement) {
    const code = window.prompt("Enter sport code (e.g., NBA):");
    if (!code || !code.trim()) {
      selectElement.value = "";
      return;
    }

    const name = window.prompt("Enter sport name (e.g., National Basketball Association):");
    if (!name || !name.trim()) {
      selectElement.value = "";
      return;
    }

    fetch("/config/sports", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ code, name }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to create sport");
        }
        return response.json();
      })
      .then((data) => {
        // Find the "+ Add sport…" option
        const addOption = selectElement.querySelector(
          'option[value="__add_sport__"]'
        );
        if (addOption) {
          // Create new option and insert before "Add sport"
          const newOption = document.createElement("option");
          newOption.value = data.code;
          newOption.textContent = data.code;
          selectElement.insertBefore(newOption, addOption);
          selectElement.value = data.code;
        }
      })
      .catch((error) => {
        console.error("Error creating sport:", error);
        alert("Failed to create sport. Please try again.");
        selectElement.value = "";
      });
  }

  // Attach change handlers for location selects
  locationSelects.forEach((select) => {
    if (select) {
      select.addEventListener("change", async function() {
        if (this.value === "__add_location__") {
          await handleAddLocation(this);
        } else {
          // Update previous value on normal changes
          locationPreviousValues.set(this, this.value);
        }
      });
    }
  });

  primarySportSelects.forEach((select) => {
    select.addEventListener("change", () => {
      if (select.value === "__add_sport__") {
        handleAddSport(select);
      }
    });
  });

  secondarySportSelects.forEach((select) => {
    select.addEventListener("change", () => {
      if (select.value === "__add_sport__") {
        handleAddSport(select);
      }
    });
  });

  // Toggle All Requests section
  const requestsBtn = document.getElementById("mgmt-view-requests-btn");
  const requestsSection = document.getElementById("mgmt-requests-section");

  if (requestsBtn && requestsSection) {
    // Ensure initial hidden state is respected
    requestsSection.style.display = requestsSection.style.display || "none";
    requestsBtn.addEventListener("click", function () {
      const isHidden =
        requestsSection.style.display === "none" ||
        requestsSection.style.display === "";
      requestsSection.style.display = isHidden ? "block" : "none";
      requestsSection.hidden = false;
      requestsBtn.textContent = isHidden ? "Hide requests" : "View requests";
    });
  }

  // Request Info Modal handlers
  const requestInfoModalBackdrop = document.getElementById("request-info-modal-backdrop");
  const requestInfoModal = document.getElementById("request-info-modal");
  const requestInfoClose = document.getElementById("request-info-close");
  const requestInfoCloseBtn = document.getElementById("request-info-close-btn");

  function openRequestInfoModal(button) {
    const requestId = button.getAttribute("data-request-id");
    if (!requestId) return;

    // Get trader name from the table row
    const row = button.closest("tr");
    const traderName = row ? row.querySelector("td:first-child").textContent.trim() : "-";

    // Populate modal with data from button attributes
    document.getElementById("request-info-trader").textContent = traderName;
    document.getElementById("request-info-alias").textContent = 
      button.getAttribute("data-request-alias") || "-";
    document.getElementById("request-info-location").textContent = 
      button.getAttribute("data-request-location") || "-";
    document.getElementById("request-info-type").textContent = 
      button.getAttribute("data-request-type") || "-";
    document.getElementById("request-info-effect").textContent = 
      button.getAttribute("data-request-effect") || "-";
    document.getElementById("request-info-date-from").textContent = 
      button.getAttribute("data-request-date-from") || "-";
    document.getElementById("request-info-date-to").textContent = 
      button.getAttribute("data-request-date-to") || "-";
    document.getElementById("request-info-days").textContent = 
      button.getAttribute("data-request-days") || "-";
    document.getElementById("request-info-shift").textContent = 
      button.getAttribute("data-request-shift") || "-";
    document.getElementById("request-info-sport").textContent = 
      button.getAttribute("data-request-sport") || "-";
    document.getElementById("request-info-destination").textContent = 
      button.getAttribute("data-request-destination") || "-";
    document.getElementById("request-info-reason").textContent = 
      button.getAttribute("data-request-reason") || "-";

    // Show modal
    if (requestInfoModalBackdrop) requestInfoModalBackdrop.removeAttribute("hidden");
    if (requestInfoModal) requestInfoModal.removeAttribute("hidden");
    document.body.style.overflow = "hidden";
  }

  function closeRequestInfoModal() {
    if (requestInfoModalBackdrop) requestInfoModalBackdrop.setAttribute("hidden", "hidden");
    if (requestInfoModal) requestInfoModal.setAttribute("hidden", "hidden");
    document.body.style.overflow = "";
  }

  // Wire up More Info buttons
  const moreInfoButtons = document.querySelectorAll(".btn-bio[data-request-id]");
  moreInfoButtons.forEach((btn) => {
    btn.addEventListener("click", function() {
      openRequestInfoModal(this);
    });
  });

  if (requestInfoClose) {
    requestInfoClose.addEventListener("click", closeRequestInfoModal);
  }

  if (requestInfoCloseBtn) {
    requestInfoCloseBtn.addEventListener("click", closeRequestInfoModal);
  }

  if (requestInfoModalBackdrop) {
    requestInfoModalBackdrop.addEventListener("click", (e) => {
      if (e.target === requestInfoModalBackdrop) {
        closeRequestInfoModal();
      }
    });
  }

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && requestInfoModal && !requestInfoModal.hasAttribute("hidden")) {
      closeRequestInfoModal();
    }
  });


  // Remove Trader Modal handlers
  const removeTraderModal = document.getElementById("removeTraderModal");
  const removeTraderModalContainer = document.getElementById("removeTraderModalContainer");
  const btnRemoveTrader = document.getElementById("btnRemoveTrader");
  const btnCloseRemoveTrader = document.getElementById("btnCloseRemoveTrader");
  const btnCancelRemoveTrader = document.getElementById("btnCancelRemoveTrader");
  const confirmRemoveBtn = document.getElementById("confirmRemoveTraderBtn");
  const removeSelect = document.getElementById("removeTraderSelect");

  function openRemoveTraderModal() {
    if (removeTraderModal) removeTraderModal.removeAttribute("hidden");
    if (removeTraderModalContainer) removeTraderModalContainer.removeAttribute("hidden");
    // Reset select
    if (removeSelect) removeSelect.value = "";
  }

  function closeRemoveTraderModal() {
    if (removeTraderModal) removeTraderModal.setAttribute("hidden", "hidden");
    if (removeTraderModalContainer) removeTraderModalContainer.setAttribute("hidden", "hidden");
  }

  if (btnRemoveTrader) {
    btnRemoveTrader.addEventListener("click", openRemoveTraderModal);
  }

  if (btnCloseRemoveTrader) {
    btnCloseRemoveTrader.addEventListener("click", closeRemoveTraderModal);
  }

  if (btnCancelRemoveTrader) {
    btnCancelRemoveTrader.addEventListener("click", closeRemoveTraderModal);
  }

  if (removeTraderModal) {
    removeTraderModal.addEventListener("click", (e) => {
      if (e.target === removeTraderModal) {
        closeRemoveTraderModal();
      }
    });
  }

  // Remove Trader: set inactive
  if (confirmRemoveBtn && removeSelect) {
    confirmRemoveBtn.addEventListener("click", async function () {
      const traderId = removeSelect.value;
      if (!traderId) {
        alert("Please select a trader");
        return;
      }

      if (!confirm("Set this trader inactive and remove from active roster?")) {
        return;
      }

      try {
        const resp = await fetch(`/traders/${traderId}/deactivate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });

        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          alert(data.detail || "Failed to set inactive");
          return;
        }

        // Reload so that active lists update
        window.location.reload();
      } catch (err) {
        console.error(err);
        alert("Error updating trader");
      }
    });
  }

  // Close Remove Trader modal on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (removeTraderModalContainer && !removeTraderModalContainer.hasAttribute("hidden")) {
        closeRemoveTraderModal();
      }
    }
  });
});

