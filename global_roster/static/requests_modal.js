// Requests Modal Management
let currentTraderId = null;
let currentTraderName = null;

// DOM elements (will be initialized in DOMContentLoaded)
let requestsModalBackdrop = null;
let requestsModal = null;
let requestsModalClose = null;
let requestsModalTitle = null;
let requestsForm = null;
let toggleExistingBtn = null;
let existingRequestsContainer = null;
let existingRequestsTbody = null;
let noRequestsMessage = null;
let errorMessage = null;
let requestTypeSelect = null;
let groupDateFrom = null;
let groupDateTo = null;
let groupShift = null;
let groupSport = null;
let groupReason = null;
let dateToInput = null;
let shiftSelect = null;
let sportInput = null;

// Request details modal elements
let requestDetailsModalBackdrop = null;
let requestDetailsModal = null;
let requestDetailsClose = null;
let requestDetailsTitle = null;
let requestDetailsDateSubmitted = null;
let requestDetailsStatus = null;
let requestDetailsApprovedBy = null;
let requestDetailsApprovedAt = null;
let requestDetailsApprovedSection = null;
let requestDetailsApprovedDateSection = null;
let requestDetailsComments = null;

// Store all requests for filtering
let allRequests = [];
let filterStatusInput = null;
let sortDateInput = null;

/**
 * Open the Requests modal for a trader
 */
function openRequestsModal(traderId, traderName) {
  currentTraderId = traderId;
  currentTraderName = traderName;
  
  // Format name: "LAST, First" -> "Requests for last, first"
  const nameLower = traderName.toLowerCase();
  requestsModalTitle.textContent = `Requests for ${nameLower}`;
  
  // Reset form
  if (requestsForm) {
    requestsForm.reset();
  }
  
  // Hide error message
  if (errorMessage) {
    errorMessage.hidden = true;
  }
  
  // Hide existing requests by default
  if (existingRequestsContainer) {
    existingRequestsContainer.hidden = true;
  }
  if (toggleExistingBtn) {
    toggleExistingBtn.textContent = "Show existing requests";
  }
  
  // Reset form visibility
  updateFormVisibility();
  
  // Show modal
  if (requestsModalBackdrop) {
    requestsModalBackdrop.hidden = false;
  }
  if (requestsModal) {
    requestsModal.hidden = false;
  }
  
  // Disable body scroll
  document.body.style.overflow = "hidden";
  
  // Fetch and populate existing requests (but keep table hidden)
  fetchExistingRequests();
}

/**
 * Close the Requests modal
 */
function closeRequestsModal() {
  // Hide modal
  if (requestsModalBackdrop) {
    requestsModalBackdrop.hidden = true;
  }
  if (requestsModal) {
    requestsModal.hidden = true;
  }
  
  // Re-enable body scroll
  document.body.style.overflow = "";
  
  currentTraderId = null;
  currentTraderName = null;
}

/**
 * Show error message
 */
function showError(message) {
  if (errorMessage) {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
    // Scroll to top
    if (requestsModal) {
      requestsModal.scrollTop = 0;
    }
  }
}

/**
 * Hide error message
 */
function hideError() {
  if (errorMessage) {
    errorMessage.hidden = true;
  }
}

/**
 * Fetch existing requests and populate the table
 */
async function fetchExistingRequests() {
  if (!currentTraderId) return;
  
  try {
    const response = await fetch(`/api/traders/${currentTraderId}/requests`);
    if (!response.ok) {
      console.error("Failed to fetch requests", response.status);
      return;
    }
    
    allRequests = await response.json();
    applyFiltersAndRender();
  } catch (err) {
    console.error("Error fetching requests", err);
  }
}

/**
 * Apply filters and sorting, then render table
 */
function applyFiltersAndRender() {
  let filteredRequests = [...allRequests];
  
  // Apply status filter if set
  if (filterStatusInput && filterStatusInput.value) {
    filteredRequests = filteredRequests.filter(req => req.status === filterStatusInput.value);
  }
  
  // Sort by date
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  if (sortDateInput && sortDateInput.value === "upcoming") {
    // Upcoming: future dates first, then past dates
    filteredRequests.sort((a, b) => {
      const dateA = new Date(a.date_from);
      const dateB = new Date(b.date_from);
      const aIsFuture = dateA >= today;
      const bIsFuture = dateB >= today;
      
      if (aIsFuture && !bIsFuture) return -1;
      if (!aIsFuture && bIsFuture) return 1;
      
      // Both future or both past - sort ascending
      return dateA - dateB;
    });
  } else {
    // Past: past dates first, then future dates
    filteredRequests.sort((a, b) => {
      const dateA = new Date(a.date_from);
      const dateB = new Date(b.date_from);
      const aIsFuture = dateA >= today;
      const bIsFuture = dateB >= today;
      
      if (!aIsFuture && bIsFuture) return -1;
      if (aIsFuture && !bIsFuture) return 1;
      
      // Both future or both past - sort descending
      return dateB - dateA;
    });
  }
  
  renderRequestsTable(filteredRequests);
}

/**
 * Render requests into the table
 */
function renderRequestsTable(requests) {
  if (!existingRequestsTbody) return;
  
  // Clear existing rows
  existingRequestsTbody.innerHTML = "";
  
  if (!requests || requests.length === 0) {
    if (noRequestsMessage) {
      noRequestsMessage.hidden = false;
    }
    return;
  }
  
  if (noRequestsMessage) {
    noRequestsMessage.hidden = true;
  }
  
  // Render each request in the table
  requests.forEach((req) => {
    // Calculate days
    const dateFrom = new Date(req.date_from);
    const dateTo = new Date(req.date_to);
    const days = Math.floor((dateTo - dateFrom) / (1000 * 60 * 60 * 24)) + 1;
    
    // Format request type
    let typeLabel = req.request_kind;
    if (req.request_kind === "REQUEST_IN") {
      typeLabel = "Request In";
    } else if (req.request_kind === "REQUEST_OFF_DAY") {
      typeLabel = "Request Off (Day)";
    } else if (req.request_kind === "REQUEST_OFF_RANGE") {
      typeLabel = "Request Off (Range)";
    }
    
    // Status badge
    const statusClass = `status-${req.status.toLowerCase()}`;
    const statusBadge = `<span class="${statusClass}">${req.status}</span>`;
    
    // View button - store request data in data attributes
    const viewButton = `<button type="button" class="btn-bio" data-request-id="${req.id}" data-request-date-from="${req.date_from}" data-request-date-to="${req.date_to}" data-request-days="${days}" data-request-type="${typeLabel}" data-request-reason="${(req.reason || '').replace(/"/g, '&quot;')}" data-request-sport="${(req.sport_code || '').replace(/"/g, '&quot;')}" data-request-shift="${(req.shift_type || '').replace(/"/g, '&quot;')}" data-request-created="${req.created_at || ''}" data-request-status="${req.status || ''}" data-request-approved-by="${(req.approved_by || '').replace(/"/g, '&quot;')}" data-request-approved-at="${req.approved_at || ''}">View</button>`;
    
    // Render table row
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${req.date_from}</td>
      <td>${days}</td>
      <td>${typeLabel}</td>
      <td>${statusBadge}</td>
      <td class="requests-actions">${viewButton}</td>
    `;
    existingRequestsTbody.appendChild(row);
  });
  
  // Attach cancel button handlers
  attachCancelHandlers();
  
  // Attach BIO button handlers
  attachBioHandlers();
}

/**
 * Attach event handlers to cancel buttons
 */
function attachCancelHandlers() {
  // Get cancel buttons from table
  const cancelButtons = document.querySelectorAll(".btn-delete[data-request-id]");
  cancelButtons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const requestId = btn.getAttribute("data-request-id");
      if (!requestId) return;
      
      if (!confirm("Are you sure you want to cancel this request?")) {
        return;
      }
      
      try {
        const response = await fetch(`/api/trader-requests/${requestId}/cancel`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });
        
        if (!response.ok) {
          throw new Error("Failed to cancel request");
        }
        
        // Refresh the requests list
        await fetchExistingRequests();
      } catch (err) {
        console.error("Error canceling request", err);
        showError("Failed to cancel request. Please try again.");
      }
    });
  });
}

/**
 * Attach event handlers to View buttons
 */
function attachBioHandlers() {
  // Get view buttons from table
  const viewButtons = document.querySelectorAll(".btn-bio[data-request-id]");
  viewButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const requestData = {
        id: btn.getAttribute("data-request-id"),
        date_from: btn.getAttribute("data-request-date-from") || "",
        date_to: btn.getAttribute("data-request-date-to") || "",
        days: btn.getAttribute("data-request-days") || "",
        type: btn.getAttribute("data-request-type") || "",
        reason: btn.getAttribute("data-request-reason") || "",
        sport_code: btn.getAttribute("data-request-sport") || "",
        shift_type: btn.getAttribute("data-request-shift") || "",
        created_at: btn.getAttribute("data-request-created") || "",
        status: btn.getAttribute("data-request-status") || "",
        approved_by: btn.getAttribute("data-request-approved-by") || "",
        approved_at: btn.getAttribute("data-request-approved-at") || ""
      };
      openRequestDetailsModal(requestData);
    });
  });
}

/**
 * Open request details modal
 */
function openRequestDetailsModal(requestData) {
  if (!requestDetailsModalBackdrop || !requestDetailsModal) return;
  
  // Format date submitted
  let dateSubmitted = "N/A";
  if (requestData.created_at) {
    try {
      const date = new Date(requestData.created_at);
      dateSubmitted = date.toLocaleString();
    } catch (err) {
      dateSubmitted = requestData.created_at;
    }
  }
  
  // Build comments text
  let comments = "";
  const parts = [];
  if (requestData.sport_code) {
    parts.push(requestData.sport_code);
  }
  if (requestData.shift_type) {
    parts.push(requestData.shift_type);
  }
  if (parts.length > 0) {
    comments = parts.join(" ");
    if (requestData.reason) {
      comments += "\n\n" + requestData.reason;
    }
  } else {
    comments = requestData.reason || "No comments";
  }
  
  // Format status with badge
  let statusDisplay = requestData.status || "N/A";
  if (requestData.status) {
    const statusClass = `status-${requestData.status.toLowerCase()}`;
    statusDisplay = `<span class="${statusClass}">${requestData.status}</span>`;
  }
  
  // Format approved date
  let approvedAtDisplay = "N/A";
  if (requestData.approved_at) {
    try {
      const date = new Date(requestData.approved_at);
      approvedAtDisplay = date.toLocaleString();
    } catch (err) {
      approvedAtDisplay = requestData.approved_at;
    }
  }
  
  // Update modal content
  const dateFromEl = document.getElementById("request-details-date-from");
  const dateToEl = document.getElementById("request-details-date-to");
  const daysEl = document.getElementById("request-details-days");
  const typeEl = document.getElementById("request-details-type");
  const cancelBtn = document.getElementById("request-details-cancel-btn");
  
  if (dateFromEl) {
    dateFromEl.textContent = requestData.date_from || "N/A";
  }
  if (dateToEl) {
    dateToEl.textContent = requestData.date_to || "N/A";
  }
  if (daysEl) {
    daysEl.textContent = requestData.days || "N/A";
  }
  if (typeEl) {
    typeEl.textContent = requestData.type || "N/A";
  }
  if (requestDetailsDateSubmitted) {
    requestDetailsDateSubmitted.textContent = dateSubmitted;
  }
  if (requestDetailsStatus) {
    requestDetailsStatus.innerHTML = statusDisplay;
  }
  
  // Show/hide approved sections based on whether request was approved/rejected
  const isApprovedOrRejected = requestData.status === "APPROVED" || requestData.status === "REJECTED";
  if (requestDetailsApprovedSection) {
    if (isApprovedOrRejected && requestData.approved_by) {
      requestDetailsApprovedSection.hidden = false;
      if (requestDetailsApprovedBy) {
        requestDetailsApprovedBy.textContent = requestData.approved_by;
      }
    } else {
      requestDetailsApprovedSection.hidden = true;
    }
  }
  if (requestDetailsApprovedDateSection) {
    if (isApprovedOrRejected && requestData.approved_at) {
      requestDetailsApprovedDateSection.hidden = false;
      if (requestDetailsApprovedAt) {
        requestDetailsApprovedAt.textContent = approvedAtDisplay;
      }
    } else {
      requestDetailsApprovedDateSection.hidden = true;
    }
  }
  
  if (requestDetailsComments) {
    requestDetailsComments.textContent = comments;
  }
  
  // Show/hide cancel button (only for PENDING requests)
  if (cancelBtn) {
    if (requestData.status === "PENDING") {
      cancelBtn.hidden = false;
      cancelBtn.setAttribute("data-request-id", requestData.id);
      // Remove existing listeners and add new one
      const newCancelBtn = cancelBtn.cloneNode(true);
      cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
      newCancelBtn.addEventListener("click", async () => {
        const requestId = newCancelBtn.getAttribute("data-request-id");
        if (!requestId) return;
        
        if (!confirm("Are you sure you want to cancel this request?")) {
          return;
        }
        
        try {
          const response = await fetch(`/api/trader-requests/${requestId}/cancel`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          });
          
          if (!response.ok) {
            throw new Error("Failed to cancel request");
          }
          
          // Close modal and refresh requests list
          closeRequestDetailsModal();
          await fetchExistingRequests();
        } catch (err) {
          console.error("Error canceling request", err);
          alert("Failed to cancel request. Please try again.");
        }
      });
    } else {
      cancelBtn.hidden = true;
    }
  }
  
  // Show modal
  requestDetailsModalBackdrop.hidden = false;
  requestDetailsModal.hidden = false;
}

/**
 * Close request details modal
 */
function closeRequestDetailsModal() {
  if (requestDetailsModalBackdrop) {
    requestDetailsModalBackdrop.hidden = true;
  }
  if (requestDetailsModal) {
    requestDetailsModal.hidden = true;
  }
}

/**
 * Toggle visibility of existing requests section
 */
function toggleExistingRequests() {
  if (!existingRequestsContainer) return;
  
  const isHidden = existingRequestsContainer.hidden;
  existingRequestsContainer.hidden = !isHidden;
  
  if (toggleExistingBtn) {
    toggleExistingBtn.textContent = isHidden ? "Hide existing requests" : "Show existing requests";
  }
}

/**
 * Update form field visibility based on request type
 */
function updateFormVisibility() {
  if (!requestTypeSelect || !groupDateFrom || !groupDateTo || !groupShift || !groupSport || !groupReason) return;
  
  const type = requestTypeSelect.value;
  
  // Hide everything first
  hide(groupDateFrom);
  hide(groupDateTo);
  hide(groupShift);
  hide(groupSport);
  hide(groupReason);
  
  if (!type) {
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

function show(el) {
  if (el) el.removeAttribute("hidden");
}

function hide(el) {
  if (el) el.setAttribute("hidden", "hidden");
}

/**
 * Handle form submission
 */
async function handleFormSubmit(e) {
  e.preventDefault();
  hideError();
  
  if (!currentTraderId) {
    showError("No trader selected");
    return;
  }
  
  const formData = new FormData(requestsForm);
  const requestKind = formData.get("request_kind");
  
  if (!requestKind) {
    showError("Please select a request type");
    return;
  }
  
  // Build payload from visible fields only
  const payload = {
    request_kind: requestKind,
    date_from: formData.get("date_from"),
  };
  
  // Add date_to only if visible and has value
  if (groupDateTo && !groupDateTo.hidden) {
    const dateTo = formData.get("date_to");
    if (dateTo) {
      payload.date_to = dateTo;
    }
  }
  
  // Add shift_type only if visible and has value
  if (groupShift && !groupShift.hidden) {
    const shiftType = formData.get("shift_type");
    if (shiftType) {
      payload.shift_type = shiftType;
    }
  }
  
  // Add sport_code only if visible and has value
  if (groupSport && !groupSport.hidden) {
    const sportCode = formData.get("sport_code");
    if (sportCode) {
      payload.sport_code = sportCode;
    }
  }
  
  // Add reason only if visible and has value
  if (groupReason && !groupReason.hidden) {
    const reason = formData.get("reason");
    if (reason) {
      payload.reason = reason;
    }
  }
  
  try {
    const response = await fetch(`/api/traders/${currentTraderId}/requests`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to create request");
    }
    
    // Reset form
    requestsForm.reset();
    updateFormVisibility();
    
    // Refresh requests list
    await fetchExistingRequests();
    
    // Show existing requests if hidden
    if (existingRequestsContainer && existingRequestsContainer.hidden) {
      toggleExistingRequests();
    }
  } catch (err) {
    console.error("Error creating request", err);
    showError(err.message || "Failed to create request. Please try again.");
  }
}

// Initialize event listeners
document.addEventListener("DOMContentLoaded", () => {
  // Initialize DOM elements
  requestsModalBackdrop = document.getElementById("requests-modal-backdrop");
  requestsModal = document.getElementById("requests-modal");
  requestsModalClose = document.getElementById("requests-modal-close");
  requestsModalTitle = document.getElementById("requests-modal-title");
  requestsForm = document.getElementById("requests-form");
  toggleExistingBtn = document.getElementById("toggle-existing-requests");
  existingRequestsContainer = document.getElementById("existing-requests-container");
  existingRequestsTbody = document.getElementById("existing-requests-tbody");
  noRequestsMessage = document.getElementById("no-requests-message");
  errorMessage = document.getElementById("requests-error-message");
  requestTypeSelect = document.getElementById("requestType");
  groupDateFrom = document.getElementById("group-date-from");
  groupDateTo = document.getElementById("group-date-to");
  groupShift = document.getElementById("group-shift");
  groupSport = document.getElementById("group-sport");
  groupReason = document.getElementById("group-reason");
  dateToInput = document.getElementById("date_to");
  shiftSelect = document.getElementById("shift_type");
  sportInput = document.getElementById("sport_code");
  
  // Request details modal elements
  requestDetailsModalBackdrop = document.getElementById("request-details-modal-backdrop");
  requestDetailsModal = document.getElementById("request-details-modal");
  requestDetailsClose = document.getElementById("request-details-close");
  requestDetailsTitle = document.getElementById("request-details-title");
  requestDetailsDateSubmitted = document.getElementById("request-details-date-submitted");
  requestDetailsStatus = document.getElementById("request-details-status");
  requestDetailsApprovedBy = document.getElementById("request-details-approved-by");
  requestDetailsApprovedAt = document.getElementById("request-details-approved-at");
  requestDetailsApprovedSection = document.getElementById("request-details-approved-section");
  requestDetailsApprovedDateSection = document.getElementById("request-details-approved-date-section");
  requestDetailsComments = document.getElementById("request-details-comments");
  
  // Filter and sort inputs
  filterStatusInput = document.getElementById("filter-status");
  sortDateInput = document.getElementById("sort-date");
  
  // Ensure modals are hidden on page load
  if (requestsModalBackdrop) {
    requestsModalBackdrop.hidden = true;
  }
  if (requestDetailsModalBackdrop) {
    requestDetailsModalBackdrop.hidden = true;
  }
  if (requestDetailsModal) {
    requestDetailsModal.hidden = true;
  }
  
  // Requests modal close button (header X button)
  if (requestsModalClose) {
    requestsModalClose.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      closeRequestsModal();
    });
  }
  
  // Requests modal footer close button
  const requestsModalFooterClose = document.getElementById("requests-modal-footer-close");
  if (requestsModalFooterClose) {
    requestsModalFooterClose.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      closeRequestsModal();
    });
  }
  
  // Requests modal backdrop click
  if (requestsModalBackdrop) {
    requestsModalBackdrop.addEventListener("click", (e) => {
      if (e.target === requestsModalBackdrop) {
        closeRequestsModal();
      }
    });
  }
  
  // Request details modal close button
  if (requestDetailsClose) {
    requestDetailsClose.addEventListener("click", closeRequestDetailsModal);
  }
  
  // Request details modal backdrop click
  if (requestDetailsModalBackdrop) {
    requestDetailsModalBackdrop.addEventListener("click", (e) => {
      if (e.target === requestDetailsModalBackdrop) {
        closeRequestDetailsModal();
      }
    });
  }
  
  // Escape key - close topmost modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (requestDetailsModalBackdrop && !requestDetailsModalBackdrop.hidden) {
        closeRequestDetailsModal();
      } else if (requestsModalBackdrop && !requestsModalBackdrop.hidden) {
        closeRequestsModal();
      }
    }
  });
  
  // Form submission
  if (requestsForm) {
    requestsForm.addEventListener("submit", handleFormSubmit);
  }
  
  // Request type change
  if (requestTypeSelect) {
    requestTypeSelect.addEventListener("change", updateFormVisibility);
  }
  
  // Toggle existing requests button
  if (toggleExistingBtn) {
    toggleExistingBtn.addEventListener("click", toggleExistingRequests);
  }
  
  // Filter and sort inputs
  if (filterStatusInput) {
    filterStatusInput.addEventListener("change", applyFiltersAndRender);
  }
  if (sortDateInput) {
    sortDateInput.addEventListener("change", applyFiltersAndRender);
  }
});

// Export for use in traders.js
window.openRequestsModal = openRequestsModal;
window.closeRequestsModal = closeRequestsModal;

