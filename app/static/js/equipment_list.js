console.log('equipment_list.js loaded');
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const filterSelect = document.getElementById('filterSelect');
    const sortSelect = document.getElementById('sortSelect');
    const tableBody = document.querySelector('tbody');
    
    if (!searchInput || !filterSelect || !sortSelect || !tableBody) {
        console.error('Missing control elements:', { searchInput, filterSelect, sortSelect, tableBody });
        return;
    }
    
    // Note: Sorting is now handled by enhanced-tables.js
    // Removed conflicting sorting logic to avoid interference
    
    searchInput.addEventListener('input', updateTable);
    filterSelect.addEventListener('change', updateTable);
    // sortSelect event listener removed - sorting now handled by enhanced-tables.js

    function updateTable() {
        try {
            console.log('Updating table:', {
                search: searchInput.value,
                filter: filterSelect.value
            });

            const rows = Array.from(tableBody.getElementsByTagName('tr'));
            const searchTerm = searchInput.value.toLowerCase();
            const filterValue = filterSelect.value.toLowerCase();

            // Filter and search
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const ppmCell = row.querySelector('td:nth-child(7)');
                const ppmValue = ppmCell ? ppmCell.textContent.trim().toLowerCase() : '';
                const matchesSearch = text.includes(searchTerm);
                const matchesFilter = !filterValue || ppmValue === filterValue;
                row.style.display = matchesSearch && matchesFilter ? '' : 'none';
            });

            // Show no results message
            if (rows.every(row => row.style.display === 'none')) {
                tableBody.innerHTML = '<tr><td colspan="16">No results found</td></tr>';
                return;
            }

            // Sorting is now handled by enhanced-tables.js

            // After updating the table, re-attach event listeners to checkboxes
            attachCheckboxEventListeners();

        } catch (error) {
            console.error('Error in updateTable:', error);
        }
    }

    // Column mapping removed - sorting now handled by enhanced-tables.js

    // Bulk delete functionality
    const selectAllCheckbox = document.getElementById('selectAll');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');

    function attachCheckboxEventListeners() {
        const itemCheckboxes = document.querySelectorAll('.item-checkbox');

        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                const row = checkbox.closest('tr');
                if (row.style.display !== 'none') {
                    checkbox.checked = selectAllCheckbox.checked;
                }
            });
            console.log('selectAllCheckbox change event');
            updateBulkDeleteButton();
        });

        itemCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                console.log('itemCheckbox change event');
                updateBulkDeleteButton();
            });
        });
    }

    attachCheckboxEventListeners();

    function updateBulkDeleteButton() {
        const checkedCount = document.querySelectorAll('.item-checkbox:checked').length;
        console.log('updateBulkDeleteButton called, checkedCount:', checkedCount);
        if (bulkDeleteBtn) {
            bulkDeleteBtn.style.display = checkedCount > 0 ? 'inline-block' : 'none';
            bulkDeleteBtn.style.visibility = checkedCount > 0 ? 'visible' : 'hidden';
        }
    }

    bulkDeleteBtn?.addEventListener('click', async function() {
        const selectedSerials = Array.from(document.querySelectorAll('.item-checkbox:checked'))
            .map(checkbox => checkbox.dataset.serial);
        
        if (!selectedSerials.length) return;

        if (!confirm(`Are you sure you want to delete ${selectedSerials.length} selected records?`)) {
            return;
        }

        try {
            const dataType = window.location.pathname.includes('ppm') ? 'ppm' : 'ocm';
            const response = await fetch(`/api/bulk_delete/${dataType}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ serials: selectedSerials })
            });

            const result = await response.json();
            
            if (result.success) {
                alert(`Successfully deleted ${result.deleted_count} records.`);
                window.location.reload();
            } else {
                alert('Error occurred during deletion.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during bulk deletion.');
        }
    });
});