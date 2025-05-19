
document.addEventListener('DOMContentLoaded', function() {
    // Filter elements
    const searchInput = document.getElementById('searchInput');
    const frequencyFilter = document.getElementById('frequencyFilter');
    const statusFilter = document.getElementById('statusFilter');
    const resetButton = document.getElementById('resetFilters');
    const tableBody = document.querySelector('#machineTable tbody');

    // Sorting elements
    const sortableHeaders = document.querySelectorAll('.sortable');
    let currentSort = {
        column: null,
        direction: 'asc'
    };

    // Filter table based on search and filter values
    function filterTable() {
        const searchTerm = searchInput.value.toLowerCase();
        const frequency = frequencyFilter.value.toLowerCase();
        const status = statusFilter.value.toLowerCase();
        const rows = tableBody.getElementsByTagName('tr');

        Array.from(rows).forEach(row => {
            const text = row.textContent.toLowerCase();

            // Get the type (PPM/OCM) from the 7th cell (index 6)
            const typeCell = row.cells[6];
            const rowType = typeCell ? typeCell.textContent.trim().toLowerCase() : '';

            // Get the status from the status badge
            const statusCell = row.cells[8];
            const statusBadge = statusCell ? statusCell.querySelector('.badge') : null;
            const rowStatus = statusBadge ? statusBadge.textContent.trim().toLowerCase() : '';

            const matchesSearch = text.includes(searchTerm);
            const matchesFrequency = !frequency ||
                                    (frequency === 'quarterly' && rowType === 'ppm') ||
                                    (frequency === 'yearly' && rowType === 'ocm');
            const matchesStatus = !status || rowStatus === status.toLowerCase();

            row.style.display = matchesSearch && matchesFrequency && matchesStatus ? '' : 'none';
        });
    }

    // Sort table based on column and direction
    function sortTable(column, direction) {
        const rows = Array.from(tableBody.getElementsByTagName('tr'));

        // Update sort icons
        sortableHeaders.forEach(header => {
            const headerColumn = header.getAttribute('data-sort');
            const icon = header.querySelector('i');

            if (headerColumn === column) {
                icon.className = direction === 'asc'
                    ? 'fas fa-sort-up ms-1'
                    : 'fas fa-sort-down ms-1';
            } else {
                icon.className = 'fas fa-sort ms-1';
            }
        });

        // Sort rows
        rows.sort((a, b) => {
            const aValue = a.getAttribute(`data-${column}`).toLowerCase();
            const bValue = b.getAttribute(`data-${column}`).toLowerCase();

            // Handle date sorting for next-maintenance
            if (column === 'next-maintenance' && aValue !== 'not scheduled' && bValue !== 'not scheduled') {
                const aDate = parseDate(aValue);
                const bDate = parseDate(bValue);

                if (aDate && bDate) {
                    return direction === 'asc' ? aDate - bDate : bDate - aDate;
                }
            }

            // Default string comparison
            if (direction === 'asc') {
                return aValue.localeCompare(bValue);
            } else {
                return bValue.localeCompare(aValue);
            }
        });

        // Reorder rows in the table
        rows.forEach(row => {
            tableBody.appendChild(row);
        });
    }

    // Helper function to parse date in DD/MM/YYYY format
    function parseDate(dateStr) {
        if (dateStr === 'Not Scheduled') return null;

        const parts = dateStr.split('/');
        if (parts.length === 3) {
            // Note: months are 0-indexed in JavaScript Date
            return new Date(parts[2], parts[1] - 1, parts[0]);
        }
        return null;
    }

    // Event listeners for filtering
    if (searchInput) searchInput.addEventListener('input', filterTable);
    if (frequencyFilter) frequencyFilter.addEventListener('change', filterTable);
    if (statusFilter) statusFilter.addEventListener('change', filterTable);
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            searchInput.value = '';
            frequencyFilter.value = '';
            statusFilter.value = '';
            filterTable();
        });
    }

    // Event listeners for sorting
    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-sort');

            // Toggle direction if clicking the same column
            let direction = 'asc';
            if (currentSort.column === column) {
                direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            }

            // Update current sort
            currentSort = {
                column: column,
                direction: direction
            };

            // Sort the table
            sortTable(column, direction);
        });
    });

    // Export table to CSV function
    function handleExportTableCSV() {
        console.log('Export function called');
        // Define headers exactly matching the table headers
        const headers = [
            "Equipment", "Model", "Serial Number", "Next Maintenance",
            "Department", "PPM / OCM", "Next Maintenance Engineer", "Status"
        ];

        // Get all visible rows from the table
        console.log('Table body:', tableBody);
        const allRows = Array.from(tableBody.querySelectorAll('tr'));
        console.log('All rows:', allRows);
        const rows = allRows
            .filter(row => row.style.display !== 'none')
            .map(row => {
                const cells = Array.from(row.cells);
                // Skip if we don't have enough cells (like header rows)
                if (cells.length < 8) return null;

                // Extract text content from each cell, handling the status badge
                return [
                    cells[0] ? cells[0].textContent.trim() || "" : "", // Equipment
                    cells[1] ? cells[1].textContent.trim() || "" : "", // Model
                    cells[2] ? cells[2].textContent.trim() || "" : "", // Serial Number
                    cells[3] ? cells[3].textContent.trim() || "" : "", // Next Maintenance
                    cells[4] ? cells[4].textContent.trim() || "" : "", // Department
                    cells[5] ? cells[5].textContent.trim() || "" : "", // PPM / OCM
                    cells[6] ? cells[6].textContent.trim() || "" : "", // Next Maintenance Engineer
                    cells[7] && cells[7].querySelector('.badge') ? cells[7].querySelector('.badge').textContent.trim() : "OK" // Status
                ];
            })
            .filter(row => row !== null); // Remove any null rows

        // Create CSV content with proper escaping for Excel
        const csvContent = [headers, ...rows]
            .map(e => e.map(val => `"${val.replace(/"/g, '""')}"`).join(","))
            .join("\n");

        // Create and download the file
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "Total_machine_list_export.csv";
        a.click();

        // Clean up
        window.URL.revokeObjectURL(url);
    }

    // Add event listener for export button
    const exportTableCSVBtn = document.getElementById('exportTableCSV');
    if (exportTableCSVBtn) {
        exportTableCSVBtn.addEventListener('click', handleExportTableCSV);
        console.log('Export button event listener added');
    } else {
        console.error('Export button not found in the DOM');
    }
});
