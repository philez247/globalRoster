document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("bio-modal");
  const closeBtn = document.getElementById("bio-close");
  const sportsDataEl = document.getElementById("sports-data");
  const ALL_SPORTS = sportsDataEl
    ? JSON.parse(sportsDataEl.dataset.sports || "[]")
    : [];

  function populateSportSelect(selectEl, includeEmpty = false) {
    if (!selectEl) return;
    const options = [];
    if (includeEmpty) {
      options.push(`<option value="">-- None --</option>`);
    }
    ALL_SPORTS.forEach((sport) => {
      options.push(`<option value="${sport.code}">${sport.code}</option>`);
    });
    selectEl.innerHTML = options.join("");
  }

  // Populate primary/secondary dropdowns on load
  populateSportSelect(document.getElementById("edit-primary-sport"), true);
  populateSportSelect(document.getElementById("edit-secondary-sport"), true);
  
  // Populate level dropdowns
  const primaryLevelSelect = document.getElementById("edit-primary-level");
  const secondaryLevelSelect = document.getElementById("edit-secondary-level");
  if (primaryLevelSelect) {
    primaryLevelSelect.innerHTML = '<option value="">-- Level --</option><option value="1">L1</option><option value="2">L2</option><option value="3">L3</option>';
  }
  if (secondaryLevelSelect) {
    secondaryLevelSelect.innerHTML = '<option value="">-- Level --</option><option value="1">L1</option><option value="2">L2</option><option value="3">L3</option>';
  }

  // Ensure modal is hidden on page load
  if (modal) modal.setAttribute("hidden", "hidden");

  let currentTraderId = null;
  let currentTraderName = null;

  function openModal(data) {
    if (!modal) {
      console.error("Modal elements not found");
      return;
    }
    
    currentTraderId = data.id;
    currentTraderName = data.name || "";
    const formatId = (id) => (id != null ? String(id).padStart(5, "0") : "");

    // Update header with trader name
    const bioNameEl = document.getElementById("bio-name");
    if (bioNameEl) {
      bioNameEl.textContent = data.name || "Trader BIO";
    }

    // Display all values in new order
    const bioNameField = document.getElementById("bio-name-field");
    if (bioNameField) bioNameField.textContent = data.name || "";
    
    const bioAlias = document.getElementById("bio-alias");
    if (bioAlias) bioAlias.textContent = data.alias || "";
    
    const bioManager = document.getElementById("bio-manager");
    if (bioManager) bioManager.textContent = data.manager || "";

    const bioLevel = document.getElementById("bio-level");
    if (bioLevel) {
      bioLevel.textContent = data.level !== null && data.level !== undefined ? data.level : "";
    }
    
    const bioUserRole = document.getElementById("bio-user-role");
    if (bioUserRole) {
      const userRole = data.user_role || "USER";
      // Format role for display (replace underscores with spaces, title case)
      const roleDisplay = userRole.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
      bioUserRole.textContent = roleDisplay;
    }
    
    const bioLocation = document.getElementById("bio-location");
    if (bioLocation) bioLocation.textContent = data.location || "";

    // Combine Days / Hours
    const bioDaysHours = document.getElementById("bio-days-hours");
    if (bioDaysHours) {
      const days = data.required_days_per_week !== null && data.required_days_per_week !== undefined
        ? data.required_days_per_week
        : "";
      const hours = data.hours_per_week !== null && data.hours_per_week !== undefined
        ? data.hours_per_week
        : "";
      if (days && hours) {
        bioDaysHours.textContent = `${days} / ${hours}`;
      } else if (days) {
        bioDaysHours.textContent = days;
      } else if (hours) {
        bioDaysHours.textContent = hours;
      } else {
        bioDaysHours.textContent = "";
      }
    }

    const bioActive = document.getElementById("bio-active");
    if (bioActive) {
      bioActive.textContent = data.is_active === false ? "No" : "Yes";
    }

    const bioPrimarySport = document.getElementById("bio-primary-sport");
    if (bioPrimarySport) bioPrimarySport.textContent = data.primary_sport || "";
    
    const bioSecondarySport = document.getElementById("bio-secondary-sport");
    if (bioSecondarySport) bioSecondarySport.textContent = data.secondary_sport || "";

    modal.removeAttribute("hidden");

    // Wire Requests button - open modal instead of navigating
    const requestsBtn = document.getElementById("btnRequests");
    if (requestsBtn) {
      requestsBtn.onclick = function () {
        // Check if openRequestsModal is available (from requests_modal.js)
        if (window.openRequestsModal) {
          window.openRequestsModal(currentTraderId, currentTraderName);
        } else {
          console.error("openRequestsModal not available");
        }
      };
    }

    // Wire Preferences button - open modal instead of navigating
    const prefBtn = document.getElementById("btnPreferences");
    if (prefBtn) {
      prefBtn.onclick = function () {
        console.log("Preferences button clicked", { currentTraderId, currentTraderName, hasFunction: !!window.openWeeklyPatternModal });
        // Check if openWeeklyPatternModal is available (from weekly_pattern_modal.js)
        if (window.openWeeklyPatternModal) {
          window.openWeeklyPatternModal(currentTraderId, currentTraderName, data);
        } else {
          console.error("openWeeklyPatternModal not available. Make sure weekly_pattern_modal.js is loaded.");
          alert("Preferences modal is not available. Please refresh the page.");
        }
      };
    }

    // Wire Edit button - opens edit modal
    const editBtn = document.getElementById("btnEdit");
    if (editBtn) {
      editBtn.onclick = function () {
        openEditModal(data);
      };
    }
  }

  function openEditModal(data) {
    const editBackdrop = document.getElementById("edit-trader-modal-backdrop");
    const editModal = document.getElementById("edit-trader-modal");

    if (!editBackdrop || !editModal) return;

    // Populate form with current values
    document.getElementById("edit-location").value = data.location || "";
    document.getElementById("edit-alias").value = data.alias || "";
    document.getElementById("edit-manager").value = data.manager || "";
    
    // Primary sport and level
    const primarySport = data.primary_sport || "";
    const primaryLevel = getSportLevel(data.sport_skills || [], primarySport);
    document.getElementById("edit-primary-sport").value = primarySport;
    document.getElementById("edit-primary-level").value = primaryLevel || "";
    
    // Secondary sport and level
    const secondarySport = data.secondary_sport || "";
    const secondaryLevel = getSportLevel(data.sport_skills || [], secondarySport);
    document.getElementById("edit-secondary-sport").value = secondarySport;
    document.getElementById("edit-secondary-level").value = secondaryLevel || "";

    // Build sports table from sport_skills
    renderSportsTable(data.sport_skills || []);

    // Show edit modal
    editBackdrop.removeAttribute("hidden");
    editModal.removeAttribute("hidden");
  }

  function getSportLevel(sportSkills, sportCode) {
    if (!sportCode) return null;
    const skill = sportSkills.find(s => s.sport_code === sportCode);
    return skill ? String(skill.sport_level) : null;
  }

  function closeEditModal() {
    const editBackdrop = document.getElementById("edit-trader-modal-backdrop");
    const editModal = document.getElementById("edit-trader-modal");

    if (editBackdrop) editBackdrop.setAttribute("hidden", "hidden");
    if (editModal) editModal.setAttribute("hidden", "hidden");
  }

  async function saveTraderChanges() {
    if (!currentTraderId) return;

    // Validate and collect skills from table
    const skills = collectSkillsFromTable();
    if (!validateSkills(skills)) {
      return;
    }

    const primarySport = document.getElementById("edit-primary-sport").value.trim() || null;
    const primaryLevel = document.getElementById("edit-primary-level").value.trim() || null;
    const secondarySport = document.getElementById("edit-secondary-sport").value.trim() || null;
    const secondaryLevel = document.getElementById("edit-secondary-level").value.trim() || null;

    // Ensure primary/secondary are in skills if set
    if (primarySport && primaryLevel) {
      const exists = skills.some(s => s.sport === primarySport);
      if (!exists) {
        skills.push({ sport: primarySport, level: primaryLevel });
      }
    }
    if (secondarySport && secondaryLevel) {
      const exists = skills.some(s => s.sport === secondarySport);
      if (!exists) {
        skills.push({ sport: secondarySport, level: secondaryLevel });
      }
    }

    const updateData = {
      location: document.getElementById("edit-location").value.trim() || null,
      alias: document.getElementById("edit-alias").value.trim() || null,
      manager: document.getElementById("edit-manager").value.trim() || null,
      primary_sport: primarySport,
      primary_level: primaryLevel ? Number(primaryLevel) : null,
      secondary_sport: secondarySport,
      secondary_level: secondaryLevel ? Number(secondaryLevel) : null,
      skills: skills,
    };

    // Normalize empty strings to null
    Object.keys(updateData).forEach(key => {
      if (updateData[key] === "" || updateData[key] === undefined) {
        updateData[key] = null;
      }
    });

    try {
      const response = await fetch(`/api/traders/${currentTraderId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update trader");
      }

      const updatedData = await response.json();
      
      // Refresh BIO modal with updated data
      openModal(updatedData);
      
      // Close edit modal
      closeEditModal();
    } catch (err) {
      console.error("Error saving trader", err);
      alert("Failed to save changes: " + err.message);
    }
  }

  function collectSkillsFromTable() {
    const skills = [];
    const rows = document.querySelectorAll("#sportsTableBody tr");
    rows.forEach((row) => {
      const sportSelect = row.querySelector(".sport-dropdown");
      const levelSelect = row.querySelector(".level-dropdown");
      if (!sportSelect || !levelSelect) return;

      const sport = sportSelect.value.trim();
      const level = levelSelect.value.trim();
      if (!sport || !level) return;

      skills.push({ sport, level });
    });
    return skills;
  }

  function validateSkills(skills) {
    // Check for duplicates
    const sports = skills.map(s => s.sport);
    const uniqueSports = new Set(sports);
    if (sports.length !== uniqueSports.size) {
      alert("Duplicate sports are not allowed. Please remove duplicates.");
      return false;
    }
    return true;
  }

  // --- Sports & Levels table helpers ---
  function renderSportsTable(skills) {
    const tbody = document.getElementById("sportsTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!Array.isArray(skills) || skills.length === 0) {
      return;
    }

    skills.forEach((skill) => {
      addSportTableRow(skill.sport_code || "", skill.sport_level ? String(skill.sport_level) : "1");
    });
  }

  function addSportTableRow(sportCode = "", level = "1") {
    const tbody = document.getElementById("sportsTableBody");
    if (!tbody) return;

    const row = document.createElement("tr");
    
    // Sport dropdown
    const sportCell = document.createElement("td");
    const sportSelect = document.createElement("select");
    sportSelect.className = "sport-dropdown";
    populateSportSelect(sportSelect, false);
    sportSelect.value = sportCode;
    sportCell.appendChild(sportSelect);
    
    // Level dropdown
    const levelCell = document.createElement("td");
    const levelSelect = document.createElement("select");
    levelSelect.className = "level-dropdown";
    levelSelect.innerHTML = '<option value="1">L1</option><option value="2">L2</option><option value="3">L3</option>';
    levelSelect.value = level;
    levelCell.appendChild(levelSelect);
    
    // Delete button
    const actionCell = document.createElement("td");
    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "delete-row";
    deleteBtn.textContent = "X";
    deleteBtn.onclick = () => row.remove();
    actionCell.appendChild(deleteBtn);
    
    row.appendChild(sportCell);
    row.appendChild(levelCell);
    row.appendChild(actionCell);
    tbody.appendChild(row);
  }

  const addSportRowBtn = document.getElementById("addSportRow");
  if (addSportRowBtn) {
    addSportRowBtn.addEventListener("click", () => addSportTableRow());
  }

  function closeModal() {
    if (modal) modal.setAttribute("hidden", "hidden");
  }

  // Wire up BIO buttons
  const bioButtons = document.querySelectorAll(".btn-bio");
  console.log("Found BIO buttons:", bioButtons.length);
  
  bioButtons.forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      const id = btn.getAttribute("data-trader-id");
      console.log("BIO button clicked, trader ID:", id);
      
      if (!id) {
        console.error("No trader ID found on button");
        return;
      }

      if (!modal) {
        console.error("Modal elements not found", { modal });
        return;
      }

      try {
        console.log("Fetching trader data from /traders/" + id);
        const response = await fetch(`/traders/${id}`);
        if (!response.ok) {
          console.error("Failed to fetch trader", response.status);
          alert("Failed to load trader information");
          return;
        }
        const data = await response.json();
        console.log("Trader data received:", data);
        openModal(data);
      } catch (err) {
        console.error("Error fetching trader", err);
        alert("Error loading trader: " + err.message);
      }
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
  }

  // Optional: close on Escape key
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      const editModal = document.getElementById("edit-trader-modal");
      if (editModal && !editModal.hidden) {
        closeEditModal();
      } else {
        closeModal();
      }
    }
  });

  // Wire edit modal buttons
  const editCloseBtn = document.getElementById("edit-trader-close");
  const editSaveBtn = document.getElementById("edit-trader-save");
  const editCancelBtn = document.getElementById("edit-trader-cancel");
  const editBackdrop = document.getElementById("edit-trader-modal-backdrop");

  if (editCloseBtn) {
    editCloseBtn.addEventListener("click", closeEditModal);
  }

  if (editSaveBtn) {
    editSaveBtn.addEventListener("click", saveTraderChanges);
  }

  if (editCancelBtn) {
    editCancelBtn.addEventListener("click", closeEditModal);
  }

  if (editBackdrop) {
    editBackdrop.addEventListener("click", (e) => {
      if (e.target === editBackdrop) {
        closeEditModal();
      }
    });
  }

  // Table sorting logic
  const table = document.getElementById("traders-table");
  if (table) {
    const headers = table.querySelectorAll("th.sortable");
    let currentSort = { key: null, direction: "asc" };

    // Find column indices
    const getColumnIndex = (key) => {
      for (let i = 0; i < headers.length; i++) {
        if (headers[i].dataset.sort === key) return i;
      }
      return -1;
    };

    const locationIndex = getColumnIndex("location");
    const nameIndex = getColumnIndex("name");

    function getCellValue(row, index) {
      return row.children[index].textContent.trim().toLowerCase();
    }

    function sortTableByIndex(index, key) {
      const tbody = table.querySelector("tbody");
      const rows = Array.from(tbody.querySelectorAll("tr"));

      // Toggle sort direction if same column
      if (currentSort.key === key) {
        currentSort.direction = currentSort.direction === "asc" ? "desc" : "asc";
      } else {
        currentSort.key = key;
        currentSort.direction = "asc";
      }

      const dirMultiplier = currentSort.direction === "asc" ? 1 : -1;

      rows.sort((a, b) => {
        const aVal = getCellValue(a, index);
        const bVal = getCellValue(b, index);
        if (aVal < bVal) return -1 * dirMultiplier;
        if (aVal > bVal) return 1 * dirMultiplier;
        return 0;
      });

      // Clear existing rows and re-append
      rows.forEach((row) => tbody.appendChild(row));

      // Update header classes
      headers.forEach((h) => {
        h.classList.remove("sort-asc", "sort-desc");
        if (h.dataset.sort === key) {
          h.classList.add(
            currentSort.direction === "asc" ? "sort-asc" : "sort-desc"
          );
        }
      });
    }

    function sortTableMultiColumn(primaryIndex, primaryKey, secondaryIndex, secondaryKey) {
      const tbody = table.querySelector("tbody");
      const rows = Array.from(tbody.querySelectorAll("tr"));

      rows.sort((a, b) => {
        // Primary sort
        const aPrimary = getCellValue(a, primaryIndex);
        const bPrimary = getCellValue(b, primaryIndex);
        if (aPrimary < bPrimary) return -1;
        if (aPrimary > bPrimary) return 1;
        
        // Secondary sort (if primary values are equal)
        const aSecondary = getCellValue(a, secondaryIndex);
        const bSecondary = getCellValue(b, secondaryIndex);
        if (aSecondary < bSecondary) return -1;
        if (aSecondary > bSecondary) return 1;
        return 0;
      });

      // Clear existing rows and re-append
      rows.forEach((row) => tbody.appendChild(row));

      // Update header classes - show both as sorted
      headers.forEach((h) => {
        h.classList.remove("sort-asc", "sort-desc");
        if (h.dataset.sort === primaryKey) {
          h.classList.add("sort-asc");
        } else if (h.dataset.sort === secondaryKey) {
          h.classList.add("sort-asc");
        }
      });
    }

    // Set default sort: Location first, then Name
    if (locationIndex >= 0 && nameIndex >= 0) {
      sortTableMultiColumn(locationIndex, "location", nameIndex, "name");
      currentSort = { key: "location", direction: "asc" };
    }

    headers.forEach((header, index) => {
      header.addEventListener("click", () => {
        const key = header.dataset.sort;
        if (!key) return;
        sortTableByIndex(index, key);
      });
    });
  }

});
