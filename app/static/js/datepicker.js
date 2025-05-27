/**
 * Date Picker Implementation
 * Initializes Flatpickr date pickers for all date input fields
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if Flatpickr is available
    if (typeof flatpickr === 'undefined') {
        console.error('Flatpickr library not loaded!');
        return;
    }
    
    // Configuration for date pickers
    const datePickerConfig = {
        dateFormat: "d/m/Y",
        allowInput: true,
        clickOpens: true,
        allowClear: true,
        locale: {
            firstDayOfWeek: 1 // Monday
        },
        parseDate: function(datestr, format) {
            // Handle DD/MM/YYYY format
            if (datestr && datestr.match(/^\d{1,2}\/\d{1,2}\/\d{4}$/)) {
                const parts = datestr.split('/');
                return new Date(parts[2], parts[1] - 1, parts[0]);
            }
            return null;
        },
        formatDate: function(date, format) {
            // Format as DD/MM/YYYY
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            return `${day}/${month}/${year}`;
        }
    };

    // Initialize date pickers for all date input fields
    initializeDatePickers();

    function initializeDatePickers() {
        // Find all date input fields
        const dateFields = [
            // OCM fields
            '#Last_Date',
            '#INSTALLATION_DATE', 
            '#WARRANTY_END',
            // PPM fields
            '#PPM_Q_I_date',
            // Training or other date fields can be added here
        ];

        dateFields.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                // Add date picker icon
                addDatePickerIcon(element);
                
                // Initialize Flatpickr
                flatpickr(element, {
                    ...datePickerConfig,
                    onReady: function(selectedDates, dateStr, instance) {
                        // Add custom styling
                        instance.calendarContainer.classList.add('custom-datepicker');
                    },
                    onChange: function(selectedDates, dateStr, instance) {
                        // Trigger change event for any form validation
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
            }
        });

        // Also initialize any elements with the 'datepicker' class
        const datepickerElements = document.querySelectorAll('.datepicker');
        datepickerElements.forEach(element => {
            if (!element._flatpickr) { // Avoid double initialization
                addDatePickerIcon(element);
                flatpickr(element, {
                    ...datePickerConfig,
                    onReady: function(selectedDates, dateStr, instance) {
                        instance.calendarContainer.classList.add('custom-datepicker');
                    },
                    onChange: function(selectedDates, dateStr, instance) {
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
            }
        });
    }

    function addDatePickerIcon(element) {
        try {
            // Check if icon already exists
            if (element.parentNode.querySelector('.datepicker-icon')) {
                return;
            }

            // Get the parent container (usually a div with form-group or similar)
            let container = element.parentNode;
            
            // If the parent is not positioned relatively, make it so
            if (getComputedStyle(container).position === 'static') {
                container.style.position = 'relative';
            }

            // Create calendar icon
            const icon = document.createElement('i');
            icon.classList.add('fas', 'fa-calendar-alt', 'datepicker-icon');
            icon.style.cssText = `
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                color: #6c757d;
                cursor: pointer;
                z-index: 10;
                pointer-events: none;
            `;

            // Insert the icon after the input element
            container.appendChild(icon);

            // Add some padding to the input to make room for the icon
            element.style.paddingRight = '35px';
        } catch (error) {
            console.error('Error adding date picker icon:', error);
        }
    }
}); 