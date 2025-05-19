# Template Column Names for All Sections

## 1. PPM (Planned Preventive Maintenance) Template

| Column Name | Description | Format | Required | Notes |
|-------------|-------------|--------|----------|-------|
| NO | Row number (auto-generated) | Integer | No | Will be auto-assigned, can be omitted in import |
| EQUIPMENT | Equipment name | Text | Yes | Can be 'n/a' if unknown |
| MODEL | Equipment model | Text | Yes | Can be 'n/a' if unknown |
| MFG_SERIAL | Manufacturer serial number | Text | Yes | **Must be unique and non-empty** |
| MANUFACTURER | Equipment manufacturer | Text | Yes | Can be 'n/a' if unknown |
| LOG_NO | Log number | Text | Yes | Can be 'n/a' if unknown |
| DEPARTMENT | Department name | Text | Yes | Can be 'n/a' if unknown |
| PPM | PPM status | 'Yes' or 'No' | Yes | Case-insensitive, will be normalized |
| PPM Q I | Q1 maintenance date | DD/MM/YYYY | Yes | **Must be in DD/MM/YYYY format** |
| Q1_ENGINEER | Q1 maintenance engineer | Text | Yes | Can be 'n/a' if unknown |
| PPM Q II | Q2 maintenance date | DD/MM/YYYY | No | Auto-generated from Q1 date |
| Q2_ENGINEER | Q2 maintenance engineer | Text | No | Can be 'n/a' if unknown |
| PPM Q III | Q3 maintenance date | DD/MM/YYYY | No | Auto-generated from Q1 date |
| Q3_ENGINEER | Q3 maintenance engineer | Text | No | Can be 'n/a' if unknown |
| PPM Q IV | Q4 maintenance date | DD/MM/YYYY | No | Auto-generated from Q1 date |
| Q4_ENGINEER | Q4 maintenance engineer | Text | No | Can be 'n/a' if unknown |

## 2. OCM (Other Corrective Maintenance) Template

| Column Name | Description | Format | Required | Notes |
|-------------|-------------|--------|----------|-------|
| NO | Row number (auto-generated) | Integer | No | Will be auto-assigned, can be omitted in import |
| EQUIPMENT | Equipment name | Text | Yes | Can be 'n/a' if unknown |
| MODEL | Equipment model | Text | Yes | Can be 'n/a' if unknown |
| MFG_SERIAL | Manufacturer serial number | Text | Yes | **Must be unique and non-empty** |
| MANUFACTURER | Equipment manufacturer | Text | Yes | Can be 'n/a' if unknown |
| LOG_NO | Log number | Text | Yes | Can be 'n/a' if unknown |
| DEPARTMENT | Department name | Text | Yes | Can be 'n/a' if unknown |
| OCM | OCM status | 'Yes' or 'No' | Yes | Case-insensitive, will be normalized |
| OCM_2024 | 2024 OCM date | Text | Yes | Can be 'n/a' if unknown |
| ENGINEER | Maintenance engineer | Text | Yes | Can be 'n/a' if unknown |
| OCM_2025 | 2025 OCM date | Text | Yes | Can be 'n/a' if unknown |

## 3. Training Template

| Column Name | Description | Format | Required | Notes |
|-------------|-------------|--------|----------|-------|
| NAME | Employee name | Text | Yes | Can be 'n/a' if unknown |
| ID | Employee ID | Text | Yes | Must be unique and non-empty |
| DEPARTMENT | Department name | Text | Yes | Can be 'n/a' if unknown |
| MACHINE 1 | Trained on machine 1 | 'Yes' or 'No' | No | Default is 'No' |
| MACHINE 1 TRAINER | Trainer for machine 1 | Text | No | Can be 'n/a' if unknown |
| MACHINE 2 | Trained on machine 2 | 'Yes' or 'No' | No | Default is 'No' |
| MACHINE 2 TRAINER | Trainer for machine 2 | Text | No | Can be 'n/a' if unknown |
| MACHINE 3 | Trained on machine 3 | 'Yes' or 'No' | No | Default is 'No' |
| MACHINE 3 TRAINER | Trainer for machine 3 | Text | No | Can be 'n/a' if unknown |
| MACHINE 4 | Trained on machine 4 | 'Yes' or 'No' | No | Default is 'No' |
| MACHINE 4 TRAINER | Trainer for machine 4 | Text | No | Can be 'n/a' if unknown |
| MACHINE 5 | Trained on machine 5 | 'Yes' or 'No' | No | Default is 'No' |
| MACHINE 5 TRAINER | Trainer for machine 5 | Text | No | Can be 'n/a' if unknown |
| MACHINE 6 | Trained on machine 6 | 'Yes' or 'No' | No | Default is 'No' |
| MACHINE 6 TRAINER | Trainer for machine 6 | Text | No | Can be 'n/a' if unknown |
| MACHINE 7 | Trained on machine 7 | 'Yes' or 'No' | No | Default is 'No' |
| MACHINE 7 TRAINER | Trainer for machine 7 | Text | No | Can be 'n/a' if unknown |

## Important Notes for All Templates

1. **Date Format**: All dates must be in DD/MM/YYYY format (e.g., 01/01/2024)
2. **Required Fields**: 
   - For PPM: MFG_SERIAL and PPM Q I (Q1 date) are strictly required
   - For OCM: MFG_SERIAL is strictly required
   - For Training: ID is strictly required
3. **Empty Fields**: Empty fields will be auto-filled with 'n/a' during import
4. **Unique Identifiers**:
   - MFG_SERIAL must be unique for PPM and OCM entries
   - ID must be unique for Training entries
5. **Case Sensitivity**: 'Yes'/'No' values are case-insensitive (yes, YES, Yes all work)
6. **First Row**: The first row must contain the column headers exactly as shown above
7. **File Format**: Files must be saved in CSV format

## Sample Data

### PPM Sample Row
```
EQUIPMENT,MODEL,MFG_SERIAL,MANUFACTURER,LOG_NO,DEPARTMENT,PPM,PPM Q I,Q1_ENGINEER,PPM Q II,Q2_ENGINEER,PPM Q III,Q3_ENGINEER,PPM Q IV,Q4_ENGINEER
Ventilator,XYZ-100,SN12345,Medical Systems Inc,LOG001,LDR,Yes,01/01/2024,John Doe,01/04/2024,Jane Smith,01/07/2024,John Doe,01/10/2024,Jane Smith
```

### OCM Sample Row
```
EQUIPMENT,MODEL,MFG_SERIAL,MANUFACTURER,LOG_NO,DEPARTMENT,OCM,OCM_2024,ENGINEER,OCM_2025
Ventilator,XYZ-100,SN12345,Medical Systems Inc,LOG001,LDR,Yes,01/06/2024,John Doe,01/06/2025
```

### Training Sample Row
```
NAME,ID,DEPARTMENT,MACHINE 1,MACHINE 1 TRAINER,MACHINE 2,MACHINE 2 TRAINER,MACHINE 3,MACHINE 3 TRAINER,MACHINE 4,MACHINE 4 TRAINER,MACHINE 5,MACHINE 5 TRAINER,MACHINE 6,MACHINE 6 TRAINER,MACHINE 7,MACHINE 7 TRAINER
John Doe,EMP001,LDR,Yes,Jane Smith,No,No,No,No,No,No,No,No,No,No,No,No
```
