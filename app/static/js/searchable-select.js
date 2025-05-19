/**
 * Makes select elements searchable by adding a search input above them.
 * 
 * Usage:
 * 1. Include this script in your HTML
 * 2. Add the 'searchable-select' class to any select element you want to make searchable
 * 3. Optionally add a 'data-placeholder' attribute to customize the search placeholder
 */
document.addEventListener('DOMContentLoaded', function() {
    // Find all select elements with the 'searchable-select' class
    const selectElements = document.querySelectorAll('select.searchable-select');
    
    selectElements.forEach(function(select) {
        makeSearchable(select);
    });
    
    /**
     * Makes a select element searchable by adding a search input above it
     * @param {HTMLSelectElement} select - The select element to make searchable
     */
    function makeSearchable(select) {
        // Create a container div to hold both the search input and the select
        const container = document.createElement('div');
        container.className = 'searchable-select-container position-relative';
        
        // Create the search input
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'form-control searchable-select-input mb-1';
        searchInput.placeholder = select.getAttribute('data-placeholder') || 'Search...';
        
        // Insert the container before the select
        select.parentNode.insertBefore(container, select);
        
        // Move the select into the container and add the search input before it
        container.appendChild(searchInput);
        container.appendChild(select);
        
        // Add event listener for the search input
        searchInput.addEventListener('input', function() {
            const searchText = this.value.toLowerCase();
            const options = select.querySelectorAll('option');
            
            options.forEach(function(option) {
                // Skip the first option if it's a placeholder (empty value)
                if (option.value === '') return;
                
                const optionText = option.textContent.toLowerCase();
                const match = optionText.includes(searchText);
                
                // Hide/show options based on search
                option.style.display = match ? '' : 'none';
            });
        });
        
        // Add CSS to make the dropdown scrollable and show/hide filtered options
        const style = document.createElement('style');
        style.textContent = `
            .searchable-select-container {
                position: relative;
            }
            .searchable-select-container select {
                width: 100%;
            }
            .searchable-select-container select option {
                padding: 8px;
            }
            .searchable-select-container select option[style*="display: none"] {
                display: none !important;
            }
        `;
        document.head.appendChild(style);
    }
});
