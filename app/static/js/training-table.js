/**
 * Training Table Dynamic Machine Display
 *
 * This script handles the dynamic display of machines based on department
 * and calculates the total number of trained machines for each employee.
 */

// Department to Machine mapping
const departmentMachines = {
    'LDR': ['BP APPARATUS', 'DELIVERY BED', 'NEBULIZER', 'OBSERVATION LIGHT', 'REFRIGERATOR'],
    'ER': ['DEFIBRILLATOR', 'VENTILATOR', 'INFUSION PUMP', 'SUCTION MACHINE'],
    'X-RAY': ['X-RAY MACHINE', 'ULTRASOUND', 'CT SCAN', 'MRI'],
    'LABORATORY': ['CENTRIFUGE', 'MICROSCOPE', 'ANALYZER', 'INCUBATOR', 'REFRIGERATOR'],
    'OR': ['ANESTHESIA MACHINE', 'SURGICAL TABLE', 'SURGICAL LIGHT', 'ELECTROSURGICAL UNIT', 'PATIENT MONITOR'],
    'ENDOSCOPY': ['ENDOSCOPE', 'LIGHT SOURCE', 'VIDEO PROCESSOR', 'WASHER'],
    'DENTAL': ['DENTAL CHAIR', 'DENTAL X-RAY', 'AUTOCLAVE', 'COMPRESSOR'],
    'CSSD': ['AUTOCLAVE', 'WASHER', 'DRYER', 'SEALER'],
    'NURSERY': ['INCUBATOR', 'PHOTOTHERAPY', 'INFANT WARMER', 'MONITOR'],
    'OB-GYN': ['ULTRASOUND', 'FETAL MONITOR', 'COLPOSCOPE', 'DELIVERY BED'],
    'OPTHA': ['SLIT LAMP', 'OPHTHALMOSCOPE', 'TONOMETER', 'PHOROPTER'],
    'ENT': ['AUDIOMETER', 'OTOSCOPE', 'ENDOSCOPE', 'MICROSCOPE'],
    'DERMA': ['LASER', 'CRYOTHERAPY', 'DERMATOSCOPE', 'ELECTROCAUTERY'],
    'PT': ['TREADMILL', 'ULTRASOUND THERAPY', 'TENS', 'PARALLEL BARS', 'EXERCISE BIKE'],
    'IVF': ['INCUBATOR', 'MICROSCOPE', 'CENTRIFUGE', 'FREEZER'],
    'GENERAL SURGERY': ['SURGICAL TABLE', 'SURGICAL LIGHT', 'ELECTROSURGICAL UNIT', 'SUCTION MACHINE'],
    'IM': ['ECG', 'NEBULIZER', 'BP APPARATUS', 'GLUCOMETER'],
    '5 A': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
    '5 B': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
    '6 A': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
    '6 B': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
    '4A': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
    '4 B': ['HOSPITAL BED', 'INFUSION PUMP', 'PATIENT MONITOR', 'SUCTION MACHINE'],
    'LAUNDRY': ['WASHER', 'DRYER', 'IRONER', 'FOLDER'],
    'PEDIA': ['INCUBATOR', 'INFANT WARMER', 'NEBULIZER', 'PHOTOTHERAPY'],
    'PLASTIC': ['LASER', 'ELECTROSURGICAL UNIT', 'LIPOSUCTION MACHINE', 'MONITOR']
};

// Legacy machine mapping (for backward compatibility)
const legacyMachineIds = {
    'sonar': 'SONAR',
    'fmx': 'FMX',
    'max': 'MAX',
    'box20': 'BOX20',
    'hex': 'HEX'
};

// Maximum number of machine columns to display
const MAX_MACHINE_COLUMNS = 7;

/**
 * Initialize the training table with dynamic machine columns
 */
function initTrainingTable() {
    const table = document.getElementById('training-table');
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr');

    // Process each employee row
    rows.forEach(row => {
        // Get department from the department cell
        const departmentCell = row.querySelector('td:nth-child(4)');
        const department = departmentCell ? departmentCell.textContent.trim() : '';

        // Get trainer from the trainer cell
        const trainerCell = row.querySelector('td:nth-child(5)');
        const trainer = trainerCell ? trainerCell.textContent.trim() : '';

        // Make sure trainer is visible
        if (trainerCell && !trainer) {
            // If trainer cell is empty but we have data in the JSON, use that
            const employeeId = row.querySelector('.item-checkbox')?.dataset.id;
            if (employeeId) {
                const employeeDataElement = document.getElementById(`employee-data-${employeeId}`);
                if (employeeDataElement) {
                    const employeeData = JSON.parse(employeeDataElement.textContent);
                    if (employeeData.TRAINER) {
                        trainerCell.textContent = employeeData.TRAINER;
                    }
                }
            }
        }

        // Get machine cells (after checkbox, name, id, department, trainer)
        const machinesCells = Array.from(row.querySelectorAll('td')).slice(5, 5 + MAX_MACHINE_COLUMNS);
        const employeeId = row.querySelector('.item-checkbox')?.dataset.id;

        if (!employeeId) return;

        // Get employee data from the data attribute
        const employeeDataElement = document.getElementById(`employee-data-${employeeId}`);
        if (!employeeDataElement) return;

        const employeeData = JSON.parse(employeeDataElement.textContent);

        // Ensure department is correctly displayed
        if (departmentCell && employeeData.DEPARTMENT && department !== employeeData.DEPARTMENT) {
            departmentCell.textContent = employeeData.DEPARTMENT;
        }

        // Get machines data, ensuring it's an object
        const machines = employeeData.MACHINES || {};

        // Get department machines or use legacy machines as fallback
        const departmentMachineList = departmentMachines[employeeData.DEPARTMENT] ||
            departmentMachines[department] ||
            Object.values(legacyMachineIds);

        // Calculate total trained machines
        let totalTrained = 0;

        // Count trained machines from the employee data
        Object.values(machines).forEach(trained => {
            if (trained === true) totalTrained++;
        });

        // Update machine cells with department-specific machines
        machinesCells.forEach((cell, index) => {
            if (index < departmentMachineList.length) {
                const machineName = departmentMachineList[index];
                const machineId = getMachineId(machineName);
                const isTrained = machines[machineId] === true;

                // Remove trainer logic from machine cell
                // let trainerName = '';
                // if (index < 7) {
                //     const trainerKey = `machine${index + 1}_trainer`;
                //     trainerName = employeeData[trainerKey] || '';
                // }

                // Update cell content with machine name and training status only
                cell.innerHTML = `
                    <div class="machine-name" title="${machineName}">${machineName}</div>
                    <div class="machine-status">
                        <span class="badge ${isTrained ? 'bg-success' : 'bg-danger'}">
                            <i class="fas fa-${isTrained ? 'check' : 'times'}"></i>
                        </span>
                    </div>
                `;
                cell.classList.add('machine-cell');
            } else {
                // Empty cell for departments with fewer machines
                cell.innerHTML = '<div class="text-muted">n/a</div>';
                cell.classList.add('machine-cell', 'empty-machine');
            }
        });

        // Add total trained machines cell
        const totalCell = document.createElement('td');
        totalCell.textContent = totalTrained;
        totalCell.classList.add('total-trained');

        // Add a class to the row based on training completion
        if (totalTrained === 0) {
            row.classList.add('training-none');
        } else if (totalTrained === departmentMachineList.length) {
            row.classList.add('training-complete');
        } else {
            row.classList.add('training-partial');
        }

        // Insert the total cell before the actions cell
        const actionsCell = row.querySelector('td:last-child');
        row.insertBefore(totalCell, actionsCell);
    });
}

/**
 * Convert a machine name to a valid machine ID
 */
function getMachineId(machineName) {
    // Check if it's a legacy machine name
    for (const [id, name] of Object.entries(legacyMachineIds)) {
        if (name.toLowerCase() === machineName.toLowerCase()) {
            return id;
        }
    }

    // Otherwise, create a new ID from the machine name
    return machineName.toLowerCase().replace(/\s+/g, '_');
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initTrainingTable);
