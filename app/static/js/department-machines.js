/**
 * Department-based machine mapping for dynamic machine checklist
 */

// Define the mapping of departments to machines
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
    'PLASTIC': ['LASER', 'ELECTROSURGICAL UNIT', 'LIPOSUCTION MACHINE', 'MONITOR'],
    'ORTHOPEDIC': [],
    'UROLOGY': [],
    'CARDIOLOGY': [],
    'OPD/WARD': [],
    'WORD': [],
    'RADIOLOGY': []
};

// Default machines for fallback
const defaultMachines = ['sonar', 'fmx', 'max', 'box20', 'hex'];

/**
 * Update the machine checklist based on the selected department
 */
function updateMachineChecklist() {
    const departmentSelect = document.getElementById('department') || document.getElementById('DEPARTMENT');
    const machinesContainer = document.getElementById('machines-container');

    if (!departmentSelect || !machinesContainer) {
        console.error('Required elements not found');
        return;
    }

    const selectedDept = departmentSelect.value;

    // Clear the current machine checklist
    machinesContainer.innerHTML = '';

    if (!selectedDept) {
        // If no department is selected, show a message
        machinesContainer.innerHTML = '<div class="alert alert-info">Please select a department to display machines.</div>';
        return;
    }

    // Get the machines for the selected department or use default
    const machines = departmentMachines[selectedDept] || defaultMachines;

    if (machines.length === 0) {
        machinesContainer.innerHTML = '<div class="alert alert-warning">No machines defined for this department.</div>';
        return;
    }

    // Create the machine checklist
    const rowsHtml = [];
    let currentRow = [];

    machines.forEach((machine, index) => {
        // Create a machine ID from the name (lowercase, no spaces)
        const machineId = machine.toLowerCase().replace(/\s+/g, '_');

        // Use machine1-7 format for the first 7 machines
        const machineNumber = index + 1;
        const machineName = machineNumber <= 7 ? `machine${machineNumber}` : `MACHINES.${machineId}`;

        // Create the trainer dropdown options
        const trainerOptions = [
            'Marlene', 'Aundre', 'Marivic', 'Fevie', 'Marily',
            'Ailene', 'Mary joy', 'Celina', 'Jijimol', 'Atma'
        ].map(trainer => `<option value="${trainer}">${trainer}</option>`).join('');

        // Create the checkbox and trainer dropdown HTML
        const checkboxHtml = `
            <div class="col-md-4 mb-3">
                <div class="machine-item">
                    <div class="machine-header">
                        <label class="machine-label">
                            <input class="form-check-input" type="checkbox" id="${machineId}" name="${machineName}" value="true">
                            <span class="machine-name"><strong>${machine}</strong></span>
                        </label>
                    </div>
                    <div class="trainer-container mt-2">
                        <label for="${machineId}_trainer" class="trainer-label">Trainer:</label>
                        <select class="form-select form-select-sm" name="${machineName}_trainer" id="${machineId}_trainer">
                            <option value="">Select Trainer</option>
                            ${trainerOptions}
                        </select>
                    </div>
                </div>
            </div>
        `;

        currentRow.push(checkboxHtml);

        // Create a new row after every 3 machines or at the end
        if (currentRow.length === 3 || index === machines.length - 1) {
            rowsHtml.push(`<div class="row mb-2">${currentRow.join('')}</div>`);
            currentRow = [];
        }
    });

    // Add the rows to the container
    machinesContainer.innerHTML = rowsHtml.join('');
}

// Initialize the machine checklist when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const departmentSelect = document.getElementById('department') || document.getElementById('DEPARTMENT');

    if (departmentSelect) {
        // Update the machine checklist when the department changes
        departmentSelect.addEventListener('change', updateMachineChecklist);

        // Initialize the machine checklist
        updateMachineChecklist();
    }
});
