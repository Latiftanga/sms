// File: static/js/base.js

/**
 * Theme Management
 */
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    
    document.documentElement.setAttribute('data-bs-theme', theme);
    updateThemeIcon(theme);
}

/**
 * Sidebar Management
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.remove('show');
    }
}

/**
 * Form Validation
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Alert Management
 */
function showAlert(message, type = 'info', duration = 5000) {
    const alertsContainer = getOrCreateAlertsContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    const iconClass = getAlertIcon(type);
    
    alertDiv.innerHTML = `
        <i class="${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alertDiv);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, duration);
    }
}

function getOrCreateAlertsContainer() {
    let container = document.getElementById('alerts-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'alerts-container';
        container.className = 'alerts-container';
        
        // Try to find the main content area first
        const mainContent = document.querySelector('.main-content');
        const containerFluid = document.querySelector('.container-fluid');
        const targetElement = mainContent || containerFluid;
        
        if (targetElement) {
            // Insert at the beginning of the content area
            targetElement.insertBefore(container, targetElement.firstChild);
        } else {
            // Fallback: insert at body
            document.body.insertBefore(container, document.body.firstChild);
        }
    }
    return container;
}

function getAlertIcon(type) {
    const icons = {
        'success': 'fas fa-check-circle',
        'danger': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    return icons[type] || icons['info'];
}

/**
 * Loading States
 */
function showLoading(element, text = 'Loading...') {
    if (!element) return;
    
    // Store original content and state
    element.setAttribute('data-original-content', element.innerHTML);
    element.setAttribute('data-original-disabled', element.disabled);
    
    // Add loading class and disable button
    element.classList.add('loading');
    element.disabled = true;
    
    // For buttons, we'll use CSS for the spinner
    // For other elements, show text with spinner
    if (!element.classList.contains('btn')) {
        element.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${text}
        `;
    }
}

function hideLoading(element) {
    if (!element) return;
    
    const originalContent = element.getAttribute('data-original-content');
    const originalDisabled = element.getAttribute('data-original-disabled');
    
    if (originalContent) {
        element.innerHTML = originalContent;
        element.classList.remove('loading');
        element.disabled = originalDisabled === 'true';
        element.removeAttribute('data-original-content');
        element.removeAttribute('data-original-disabled');
    }
}

/**
 * Table Utilities
 */
function initializeDataTable(tableId, options = {}) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    // Add search functionality
    addTableSearch(table);
    
    // Add sorting functionality
    addTableSort(table);
}

function addTableSearch(table) {
    const searchInput = table.closest('.card').querySelector('.search-form input');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

function addTableSort(table) {
    const headers = table.querySelectorAll('th[data-sortable]');
    
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(table, this);
        });
    });
}

function sortTable(table, header) {
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const isAscending = !header.classList.contains('sort-asc');
    
    // Remove previous sort classes
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add current sort class
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aText = a.children[columnIndex].textContent.trim();
        const bText = b.children[columnIndex].textContent.trim();
        
        const comparison = aText.localeCompare(bText, undefined, { numeric: true });
        return isAscending ? comparison : -comparison;
    });
    
    // Reorder rows in DOM
    const tbody = table.querySelector('tbody');
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Form Helpers
 */
function addLoadingToForms() {
    // Add loading state to all forms with submit buttons
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Skip forms that already have custom loading handlers
        if (form.hasAttribute('data-custom-loading')) return;
        
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                // Get custom loading text from button or form
                const loadingText = submitButton.getAttribute('data-loading-text') || 
                                 form.getAttribute('data-loading-text') || 
                                 'Processing...';
                showLoading(submitButton, loadingText);
            }
        });
    });
}

function addCustomFormLoading(formSelector, options = {}) {
    const form = document.querySelector(formSelector);
    if (!form) return;
    
    // Mark form as having custom loading
    form.setAttribute('data-custom-loading', 'true');
    
    const {
        loadingText = 'Processing...',
        buttonSelector = 'button[type="submit"]',
        onSubmit = null,
        onComplete = null
    } = options;
    
    form.addEventListener('submit', function(e) {
        const submitButton = form.querySelector(buttonSelector);
        if (submitButton && !submitButton.disabled) {
            showLoading(submitButton, loadingText);
            
            if (onSubmit) {
                onSubmit(form, submitButton);
            }
            
            // Auto-hide loading after form submission (fallback)
            setTimeout(() => {
                if (submitButton.classList.contains('loading')) {
                    hideLoading(submitButton);
                    if (onComplete) {
                        onComplete(form, submitButton);
                    }
                }
            }, 10000); // 10 second fallback
        }
    });
}

function submitFormWithAjax(formId, successCallback, errorCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const submitButton = form.querySelector('button[type="submit"]');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (submitButton) {
            showLoading(submitButton, 'Saving...');
        }
        
        const formData = new FormData(form);
        
        fetch(form.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (submitButton) {
                hideLoading(submitButton);
            }
            
            if (data.success) {
                if (successCallback) {
                    successCallback(data);
                } else {
                    showAlert(data.message || 'Operation completed successfully', 'success');
                }
            } else {
                if (errorCallback) {
                    errorCallback(data);
                } else {
                    showAlert(data.message || 'An error occurred', 'danger');
                }
            }
        })
        .catch(error => {
            if (submitButton) {
                hideLoading(submitButton);
            }
            
            if (errorCallback) {
                errorCallback({ message: error.message });
            } else {
                showAlert('A network error occurred', 'danger');
            }
        });
    });
}

/**
 * Initialization
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initializeTheme();
    
    // Add loading states to forms
    addLoadingToForms();
    
    // Initialize sidebar toggle
    const sidebarToggle = document.querySelector('.navbar-toggler');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.querySelector('.navbar-toggler');
        
        if (sidebar && sidebar.classList.contains('show')) {
            if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                closeSidebar();
            }
        }
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert.querySelector('.btn-close')) {
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 5000);
            }
        });
    }, 100);
});

// Export for use in other scripts
window.SMS = {
    toggleTheme,
    showAlert,
    showLoading,
    hideLoading,
    validateForm,
    submitFormWithAjax,
    initializeDataTable,
    addLoadingToForms,
    addCustomFormLoading
};