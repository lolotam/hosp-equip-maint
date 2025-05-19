/**
 * Enhanced Tables JavaScript
 * Adds row numbering, sorting, and column filtering to data tables
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize enhanced tables
    initEnhancedTables();
});

/**
 * Initialize enhanced tables with row numbering, sorting, and filtering
 */
function initEnhancedTables() {
    const tables = document.querySelectorAll('table.enhanced-table');
    
    tables.forEach(table => {
        const tableId = table.id || 'table-' + Math.random().toString(36).substr(2, 9);
        table.id = tableId;
        
        // Add data-table-id to all elements within the table
        const elements = table.querySelectorAll('*');
        elements.forEach(el => {
            el.dataset.tableId = tableId;
        });
        
        // Initialize row numbering
        initRowNumbering(table);
        
        // Initialize column sorting
        initColumnSorting(table);
        
        // Initialize column filtering
        initColumnFiltering(table);
        
        // Add clear filters button
        addClearFiltersButton(table);
    });
}

/**
 * Initialize row numbering for a table
 */
function initRowNumbering(table) {
    // Get the header row
    const headerRow = table.querySelector('thead tr');
    if (!headerRow) return;
    
    // Add row number header
    const rowNumberHeader = document.createElement('th');
    rowNumberHeader.textContent = '#';
    rowNumberHeader.classList.add('row-number-column');
    rowNumberHeader.style.width = '50px';
    headerRow.insertBefore(rowNumberHeader, headerRow.firstChild);
    
    // Add row numbers to each row
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach((row, index) => {
        const rowNumberCell = document.createElement('td');
        rowNumberCell.textContent = index + 1;
        rowNumberCell.classList.add('row-number');
        row.insertBefore(rowNumberCell, row.firstChild);
    });
}

/**
 * Update row numbering after filtering or sorting
 */
function updateRowNumbering(table) {
    const visibleRows = Array.from(table.querySelectorAll('tbody tr')).filter(row => {
        return row.style.display !== 'none';
    });
    
    visibleRows.forEach((row, index) => {
        const rowNumberCell = row.querySelector('td.row-number');
        if (rowNumberCell) {
            rowNumberCell.textContent = index + 1;
        }
    });
}

/**
 * Initialize column sorting for a table
 */
function initColumnSorting(table) {
    const headerCells = table.querySelectorAll('thead th:not(.row-number-column):not(.no-sort)');
    
    headerCells.forEach((headerCell, index) => {
        // Add sort icon
        const sortIcon = document.createElement('i');
        sortIcon.className = 'fas fa-sort ms-1';
        headerCell.appendChild(sortIcon);
        
        // Make header cell sortable
        headerCell.classList.add('sortable');
        headerCell.dataset.sortDirection = 'none';
        headerCell.dataset.columnIndex = index + 1; // +1 because of row number column
        
        // Add click event for sorting
        headerCell.addEventListener('click', function() {
            const columnIndex = parseInt(this.dataset.columnIndex);
            const currentDirection = this.dataset.sortDirection;
            
            // Reset all other headers
            headerCells.forEach(cell => {
                if (cell !== headerCell) {
                    cell.dataset.sortDirection = 'none';
                    cell.querySelector('i').className = 'fas fa-sort ms-1';
                }
            });
            
            // Set new sort direction
            let newDirection = 'asc';
            if (currentDirection === 'asc') {
                newDirection = 'desc';
            } else if (currentDirection === 'desc') {
                newDirection = 'none';
            }
            
            this.dataset.sortDirection = newDirection;
            
            // Update sort icon
            if (newDirection === 'asc') {
                sortIcon.className = 'fas fa-sort-up ms-1';
            } else if (newDirection === 'desc') {
                sortIcon.className = 'fas fa-sort-down ms-1';
            } else {
                sortIcon.className = 'fas fa-sort ms-1';
            }
            
            // Sort the table
            sortTable(table, columnIndex, newDirection);
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(table, columnIndex, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    if (direction === 'none') {
        // Reset to original order
        const originalRows = Array.from(rows).sort((a, b) => {
            const aIndex = parseInt(a.dataset.originalIndex || 0);
            const bIndex = parseInt(b.dataset.originalIndex || 0);
            return aIndex - bIndex;
        });
        
        // Clear tbody and append rows in original order
        tbody.innerHTML = '';
        originalRows.forEach(row => tbody.appendChild(row));
    } else {
        // Store original index if not already stored
        rows.forEach((row, index) => {
            if (!row.dataset.originalIndex) {
                row.dataset.originalIndex = index;
            }
        });
        
        // Sort rows
        const sortedRows = rows.sort((a, b) => {
            const aValue = a.cells[columnIndex]?.textContent.trim() || '';
            const bValue = b.cells[columnIndex]?.textContent.trim() || '';
            
            // Check if values are dates (DD/MM/YYYY format)
            const aDate = parseDate(aValue);
            const bDate = parseDate(bValue);
            
            if (aDate && bDate) {
                return direction === 'asc' ? aDate - bDate : bDate - aDate;
            }
            
            // Check if values are numbers
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return direction === 'asc' ? aNum - bNum : bNum - aNum;
            }
            
            // Default string comparison
            return direction === 'asc' 
                ? aValue.localeCompare(bValue) 
                : bValue.localeCompare(aValue);
        });
        
        // Clear tbody and append sorted rows
        tbody.innerHTML = '';
        sortedRows.forEach(row => tbody.appendChild(row));
    }
    
    // Update row numbering
    updateRowNumbering(table);
}

/**
 * Parse date in DD/MM/YYYY format
 */
function parseDate(dateStr) {
    const parts = dateStr.split('/');
    if (parts.length === 3) {
        // Note: months are 0-indexed in JavaScript Date
        return new Date(parts[2], parts[1] - 1, parts[0]);
    }
    return null;
}

/**
 * Initialize column filtering for a table
 */
function initColumnFiltering(table) {
    // Create filter row
    const headerRow = table.querySelector('thead tr');
    if (!headerRow) return;
    
    const filterRow = document.createElement('tr');
    filterRow.classList.add('filter-row');
    
    // Add filter cells
    const headerCells = headerRow.querySelectorAll('th');
    headerCells.forEach((headerCell, index) => {
        const filterCell = document.createElement('th');
        
        // Skip filter for row number column and no-filter columns
        if (headerCell.classList.contains('row-number-column') || 
            headerCell.classList.contains('no-filter')) {
            filterCell.classList.add('no-filter');
            filterRow.appendChild(filterCell);
            return;
        }
        
        // Create filter input
        const columnName = headerCell.textContent.trim().replace(/[^\w\s]/gi, '');
        const isDropdown = headerCell.classList.contains('dropdown-filter');
        
        if (isDropdown) {
            // Create dropdown filter
            const select = document.createElement('select');
            select.classList.add('form-select', 'form-select-sm', 'column-filter');
            select.dataset.columnIndex = index;
            
            // Add default option
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'All';
            select.appendChild(defaultOption);
            
            // Get unique values for this column
            const uniqueValues = getUniqueColumnValues(table, index);
            uniqueValues.forEach(value => {
                if (value.trim()) {
                    const option = document.createElement('option');
                    option.value = value;
                    option.textContent = value;
                    select.appendChild(option);
                }
            });
            
            select.addEventListener('change', function() {
                filterTable(table);
            });
            
            filterCell.appendChild(select);
        } else {
            // Create text input filter
            const input = document.createElement('input');
            input.type = 'text';
            input.classList.add('form-control', 'form-control-sm', 'column-filter');
            input.placeholder = `Filter ${columnName}`;
            input.dataset.columnIndex = index;
            
            input.addEventListener('input', function() {
                filterTable(table);
            });
            
            filterCell.appendChild(input);
        }
        
        filterRow.appendChild(filterCell);
    });
    
    // Add filter row to table head
    const thead = table.querySelector('thead');
    thead.appendChild(filterRow);
}

/**
 * Get unique values for a table column
 */
function getUniqueColumnValues(table, columnIndex) {
    const rows = table.querySelectorAll('tbody tr');
    const values = new Set();
    
    rows.forEach(row => {
        const cell = row.cells[columnIndex];
        if (cell) {
            values.add(cell.textContent.trim());
        }
    });
    
    return Array.from(values).sort();
}

/**
 * Filter table based on column filters
 */
function filterTable(table) {
    const filters = table.querySelectorAll('.column-filter');
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        let showRow = true;
        
        filters.forEach(filter => {
            const columnIndex = parseInt(filter.dataset.columnIndex);
            const filterValue = filter.value.toLowerCase();
            
            if (filterValue) {
                const cell = row.cells[columnIndex];
                const cellValue = cell ? cell.textContent.trim().toLowerCase() : '';
                
                if (!cellValue.includes(filterValue)) {
                    showRow = false;
                }
            }
        });
        
        row.style.display = showRow ? '' : 'none';
    });
    
    // Update row numbering
    updateRowNumbering(table);
}

/**
 * Add clear filters button
 */
function addClearFiltersButton(table) {
    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('clear-filters-container', 'mb-2');
    
    // Create clear filters button
    const clearButton = document.createElement('button');
    clearButton.type = 'button';
    clearButton.classList.add('btn', 'btn-sm', 'btn-outline-secondary');
    clearButton.innerHTML = '<i class="fas fa-times me-1"></i> Clear Filters';
    clearButton.style.display = 'none'; // Hide initially
    
    clearButton.addEventListener('click', function() {
        // Clear all filters
        const filters = table.querySelectorAll('.column-filter');
        filters.forEach(filter => {
            if (filter.tagName === 'SELECT') {
                filter.selectedIndex = 0;
            } else {
                filter.value = '';
            }
        });
        
        // Reset table
        filterTable(table);
        
        // Hide clear button
        this.style.display = 'none';
    });
    
    buttonContainer.appendChild(clearButton);
    
    // Add button container before table
    table.parentNode.insertBefore(buttonContainer, table);
    
    // Show/hide clear button based on filters
    const filters = table.querySelectorAll('.column-filter');
    filters.forEach(filter => {
        filter.addEventListener('input', function() {
            const anyFilterActive = Array.from(filters).some(f => f.value);
            clearButton.style.display = anyFilterActive ? 'inline-block' : 'none';
        });
        
        filter.addEventListener('change', function() {
            const anyFilterActive = Array.from(filters).some(f => f.value);
            clearButton.style.display = anyFilterActive ? 'inline-block' : 'none';
        });
    });
}
