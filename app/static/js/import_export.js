document.addEventListener('DOMContentLoaded', () => {
    const importForm = document.getElementById('importForm');
    const exportButtons = document.querySelectorAll('.export-button');
    const importResult = document.getElementById('importResult');
    const importProgress = document.getElementById('importProgress');

    if (importForm) {
        importForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const formData = new FormData(importForm);
            const dataType = formData.get('data_type'); // Get data_type from form
            const file = formData.get('file'); // Get file from form

            if (!file) {
                importResult.innerHTML = '<div class="alert alert-danger">Please select a file.</div>';
                return;
            }

            try {
                importProgress.innerHTML = '<div class="alert alert-info">Importing... Please wait.</div>';
                const response = await fetch(`/api/import/${dataType}`, {
                    method: 'POST',
                    body: formData,
                });

                const data = await response.json();
                if (response.ok) {
                    let resultHtml = `<div class="alert alert-success">${data.message}</div>`;
                    resultHtml += `<p>Total Rows: ${data.stats.total_rows}</p>`;
                    resultHtml += `<p>Imported: ${data.stats.imported}</p>`;
                    resultHtml += `<p>Skipped: ${data.stats.skipped}</p>`;
                    resultHtml += `<p>Errors: ${data.stats.errors}</p>`;
                    if (data.stats.skipped_details && data.stats.skipped_details.length > 0) {
                        resultHtml += `<h5>Skipped Details:</h5><ul>`;
                        data.stats.skipped_details.forEach(detail => {
                            resultHtml += `<li>${detail}</li>`;
                        });
                        resultHtml += `</ul>`;
                    }
                    if (data.stats.error_details && data.stats.error_details.length > 0) {
                        resultHtml += `<h5>Error Details:</h5><ul>`;
                        data.stats.error_details.forEach(detail => {
                            resultHtml += `<li>${detail}</li>`;
                        });
                        resultHtml += `</ul>`;
                    }

                    importResult.innerHTML = resultHtml;
                } else {
                    importResult.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                }
            } catch (error) {
                console.error('Error during import:', error);
                importResult.innerHTML = '<div class="alert alert-danger">An unexpected error occurred during import.</div>';
            } finally {
                importProgress.innerHTML = '';
            }
        });
    }

    exportButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const dataType = button.getAttribute('data-type');
            try {
                const response = await fetch(`/api/export/${dataType}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${dataType}_export.csv`;
                    a.click();
                }
            } catch (error) {
                console.error('Error during export:', error);
            }
        });
    });
});
