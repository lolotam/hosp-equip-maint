/**
 * Enhanced UI/UX JavaScript for Hospital Equipment Maintenance System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();

    // Initialize loading indicators
    initLoadingIndicators();

    // Add card hover effects
    initCardHoverEffects();

    // Add form validation styling
    initFormValidation();

    // Initialize modals
    initModals();

    // Set active navigation item
    setActiveNavItem();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize loading indicators for data fetches
 */
function initLoadingIndicators() {
    // Add loading indicator to all buttons that trigger data loading
    const dataButtons = document.querySelectorAll('.btn[data-action="fetch"]');
    dataButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                // Show loading spinner
                const spinner = document.createElement('div');
                spinner.className = 'loading-spinner-container text-center py-5';
                spinner.innerHTML = `
                    <div class="loading-spinner"></div>
                    <p class="mt-3">Loading data...</p>
                `;

                targetElement.innerHTML = '';
                targetElement.appendChild(spinner);
            }
        });
    });
}

/**
 * Initialize card hover effects
 */
function initCardHoverEffects() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.15)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        });
    });
}

/**
 * Initialize form validation styling
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            this.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize modal functionality
 */
function initModals() {
    // Add modal trigger functionality to buttons with data-modal attribute
    const modalTriggers = document.querySelectorAll('[data-modal]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(event) {
            event.preventDefault();

            const modalId = this.getAttribute('data-modal');
            const modalElement = document.getElementById(modalId);

            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
        });
    });
}

/**
 * Show a loading spinner in the specified element
 * @param {string} elementId - The ID of the element to show the spinner in
 * @param {string} message - Optional message to display with the spinner
 */
function showLoadingSpinner(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-4">
                <div class="loading-spinner"></div>
                <p class="mt-3">${message}</p>
            </div>
        `;
    }
}

/**
 * Hide the loading spinner and restore content
 * @param {string} elementId - The ID of the element containing the spinner
 * @param {string} content - The content to display after removing the spinner
 */
function hideLoadingSpinner(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = content;
    }
}

/**
 * Add a tooltip to an element
 * @param {HTMLElement} element - The element to add the tooltip to
 * @param {string} title - The tooltip text
 */
function addTooltip(element, title) {
    element.setAttribute('data-bs-toggle', 'tooltip');
    element.setAttribute('data-bs-placement', 'top');
    element.setAttribute('title', title);
    new bootstrap.Tooltip(element);
}

/**
 * Set the active navigation item based on the current URL
 */
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.classList.remove('active');
        const href = link.getAttribute('href');

        if (currentPath === href) {
            link.classList.add('active');
        } else if (href !== '/' && currentPath.includes(href)) {
            link.classList.add('active');
        }
    });
}

/**
 * Create a modal dialog
 * @param {string} id - The ID for the modal
 * @param {string} title - The modal title
 * @param {string} body - The modal body content (HTML)
 * @param {Array} buttons - Array of button objects {text, class, handler}
 * @returns {HTMLElement} The created modal element
 */
function createModal(id, title, body, buttons = []) {
    // Create modal container
    const modalContainer = document.createElement('div');
    modalContainer.className = 'modal fade';
    modalContainer.id = id;
    modalContainer.tabIndex = -1;
    modalContainer.setAttribute('aria-labelledby', `${id}Label`);
    modalContainer.setAttribute('aria-hidden', 'true');

    // Create modal HTML
    modalContainer.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="${id}Label">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    ${body}
                </div>
                <div class="modal-footer">
                    ${buttons.map(btn => `
                        <button type="button" class="btn ${btn.class || 'btn-secondary'}" id="${id}-${btn.text.toLowerCase().replace(/\s+/g, '-')}">${btn.text}</button>
                    `).join('')}
                </div>
            </div>
        </div>
    `;

    // Add to document
    document.body.appendChild(modalContainer);

    // Add event handlers for buttons
    buttons.forEach(btn => {
        const btnElement = document.getElementById(`${id}-${btn.text.toLowerCase().replace(/\s+/g, '-')}`);
        if (btnElement && btn.handler) {
            btnElement.addEventListener('click', btn.handler);
        }
    });

    return modalContainer;
}
