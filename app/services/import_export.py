"""
Service for importing and exporting data.
"""
import logging
import os
from io import StringIO
from typing import List, Dict, Any, Literal, Tuple
import json

import pandas as pd
from pydantic import ValidationError

from app.models.ppm import PPMEntry
from app.models.ocm import OCMEntry
from app.services.data_service import DataService


logger = logging.getLogger(__name__)


class ImportExportService:
    """Service for handling import and export operations."""
    
    @staticmethod
    def export_to_csv(data_type: Literal['ppm', 'ocm'], output_path: str = None) -> Tuple[bool, str, str]:
        """Export data to CSV file.
        
        Args:
            data_type: Type of data to export ('ppm' or 'ocm')
            output_path: Path to save the CSV file (optional)
            
        Returns:
            Tuple of (success, message, csv_content)
        """
        try:
            # Load data
            data = DataService.load_data(data_type)
            
            if not data:
                return False, f"No {data_type.upper()} data to export", ""
            
            # Prepare data for export
            flat_data = []
            
            for entry in data:
                flat_entry = {
                    'NO': entry.get('NO'),
                    'EQUIPMENT': entry.get('EQUIPMENT'),
                    'MODEL': entry.get('MODEL'),
                    'MFG_SERIAL': entry.get('MFG_SERIAL'),
                    'MANUFACTURER': entry.get('MANUFACTURER'),
                    'LOG_NO': entry.get('LOG_NO'),
                    'PPM': entry.get('PPM', ''),
                    'OCM': entry.get('OCM', '')
                }
                
                if data_type == 'ppm':
                    # Map quarter data
                    quarter_map = [
                        ('I', 1, 'PPM_Q_I'),
                        ('II', 2, 'PPM_Q_II'),
                        ('III', 3, 'PPM_Q_III'),
                        ('IV', 4, 'PPM_Q_IV')
                    ]
                    
                    for roman, num, q_key in quarter_map:
                        q_data = entry.get(q_key, {})
                        flat_entry[f'PPM Q {roman}'] = q_data.get('date', '')
                        flat_entry[f'Q{num}_ENGINEER'] = q_data.get('engineer', '')
                elif data_type == 'ocm':
                    flat_entry['OCM_2024'] = entry.get('OCM_2024', '')
                    flat_entry['ENGINEER'] = entry.get('ENGINEER', '')
                    flat_entry['OCM_2025'] = entry.get('OCM_2025', '')
                
                flat_data.append(flat_entry)
            
            # Define column order
            if data_type == 'ppm':
                columns_order = [
                    'NO', 'EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'PPM', 'OCM',
                    'PPM Q I', 'Q1_ENGINEER',
                    'PPM Q II', 'Q2_ENGINEER',
                    'PPM Q III', 'Q3_ENGINEER',
                    'PPM Q IV', 'Q4_ENGINEER'
                ]
            else:  # OCM
                columns_order = [
                    'NO', 'EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'PPM', 'OCM',
                    'OCM_2024', 'ENGINEER', 'OCM_2025'
                ]
            
            # Create DataFrame and export
            df = pd.DataFrame(flat_data)
            
            # Ensure all columns exist
            for col in columns_order:
                if col not in df.columns:
                    df[col] = ''
            
            # Reorder columns
            df = df[columns_order]
            
            # Export to CSV
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            if output_path:
                df.to_csv(output_path, index=False)
                return True, f"Exported {len(data)} {data_type.upper()} entries to {output_path}", csv_content
            else:
                return True, f"Exported {len(data)} {data_type.upper()} entries", csv_content
                
        except Exception as e:
            logger.error(f"Error exporting {data_type} data: {str(e)}")
            return False, f"Error exporting {data_type.upper()} data: {str(e)}", ""

    @staticmethod
    def import_from_csv(data_type: Literal['ppm', 'ocm'], file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Import data from CSV file.
        
        Args:
            data_type: Type of data to import ('ppm' or 'ocm')
            file_path: Path to CSV file
            
        Returns:
            Tuple of (success, message, import_stats)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}", {}
            
            # Load current data
            current_data = DataService.load_data(data_type)
            
            # Read CSV
            df = pd.read_csv(file_path)
            df.fillna('', inplace=True)
            
            # Drop NO column if present
            if 'NO' in df.columns:
                df = df.drop(columns=['NO'])
            
            # Convert all columns to string
            df = df.astype(str)
            
            # Process rows
            new_entries = []
            skipped_entries = []
            error_entries = []
            
            for idx, row in df.iterrows():
                row_dict = row.to_dict()
                
                try:
                    if data_type == 'ppm':
                        # Process PPM entry
                        ppm_mapping = {
                            'I': ('PPM Q I', 'Q1_ENGINEER'),
                            'II': ('PPM Q II', 'Q2_ENGINEER'),
                            'III': ('PPM Q III', 'Q3_ENGINEER'),
                            'IV': ('PPM Q IV', 'Q4_ENGINEER'),
                        }
                        
                        combined = {}
                        quarters_valid = True
                        
                        for q_key, (date_col, eng_col) in ppm_mapping.items():
                            date_val = row_dict.get(date_col, '').strip()
                            eng_val = row_dict.get(eng_col, '').strip()
                            
                            # If date is empty, mark this entry for skipping
                            if not date_val:
                                quarters_valid = False
                                break
                            
                            combined[f'PPM_Q_{q_key}'] = {
                                'date': date_val,
                                'engineer': eng_val or 'Not Assigned'  # Default engineer if empty
                            }
                        
                        if not quarters_valid:
                            skipped_entries.append(f"Row {idx+2}: Missing quarter date(s)")
                            continue
                        
                        # Process required fields
                        required_fields = ['EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'PPM']
                        fields_valid = True
                        
                        for field in required_fields:
                            value = row_dict.get(field, '')
                            if not str(value).strip():
                                fields_valid = False
                                skipped_entries.append(f"Row {idx+2}: Missing required field '{field}'")
                                break
                        
                        if not fields_valid:
                            continue
                        
                        # Map the rest of the fields
                        combined.update({
                            'EQUIPMENT': row_dict['EQUIPMENT'].strip(),
                            'MODEL': row_dict['MODEL'].strip(),
                            'MFG_SERIAL': row_dict['MFG_SERIAL'].strip(),
                            'MANUFACTURER': row_dict['MANUFACTURER'].strip(),
                            'LOG_NO': str(row_dict['LOG_NO']).strip(),
                            'PPM': row_dict['PPM'].strip(),
                            'OCM': row_dict.get('OCM', '').strip(),
                        })
                        
                        # Normalize PPM value
                        if combined['PPM'].lower() == 'yes':
                            combined['PPM'] = 'Yes'
                        elif combined['PPM'].lower() == 'no':
                            combined['PPM'] = 'No'
                        else:
                            skipped_entries.append(f"Row {idx+2}: Invalid PPM value '{combined['PPM']}'")
                            continue
                        
                        # Validate using Pydantic model
                        entry = PPMEntry(**combined).model_dump()
                        
                    else:  # OCM
                        # Process OCM entry
                        combined = {
                            'EQUIPMENT': row_dict['EQUIPMENT'].strip(),
                            'MODEL': row_dict['MODEL'].strip(),
                            'MFG_SERIAL': row_dict['MFG_SERIAL'].strip(),
                            'MANUFACTURER': row_dict['MANUFACTURER'].strip(),
                            'LOG_NO': str(row_dict['LOG_NO']).strip(),
                            'PPM': row_dict.get('PPM', '').strip(),
                            'OCM': row_dict['OCM'].strip(),
                            'OCM_2024': row_dict.get('OCM_2024', '').strip(),
                            'ENGINEER': row_dict.get('ENGINEER', '').strip(),
                            'OCM_2025': row_dict.get('OCM_2025', '').strip(),
                        }
                        
                        # Normalize OCM value
                        if combined['OCM'].lower() == 'yes':
                            combined['OCM'] = 'Yes'
                        elif combined['OCM'].lower() == 'no':
                            combined['OCM'] = 'No'
                        else:
                            skipped_entries.append(f"Row {idx+2}: Invalid OCM value '{combined['OCM']}'")
                            continue
                        
                        # Validate using Pydantic model
                        entry = OCMEntry(**combined).model_dump()
                    
                    # Check for duplicate MFG_SERIAL in existing data and new entries
                    mfg_serial = entry['MFG_SERIAL']
                    is_duplicate = False
                    
                    for existing_entry in current_data:
                        if existing_entry['MFG_SERIAL'] == mfg_serial:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        for new_entry in new_entries:
                            if new_entry['MFG_SERIAL'] == mfg_serial:
                                is_duplicate = True
                                break
                    
                    if is_duplicate:
                        skipped_entries.append(f"Row {idx+2}: Duplicate MFG_SERIAL '{mfg_serial}'")
                        continue
                    
                    # Add to new entries
                    new_entries.append(entry)
                    
                except ValidationError as e:
                    error_entries.append(f"Row {idx+2}: Validation error - {str(e)}")
                except Exception as e:
                    error_entries.append(f"Row {idx+2}: Unexpected error - {str(e)}")
            
            # If any entries were processed, add them to the current data and save
            if new_entries:
                current_data.extend(new_entries)
                reindexed_data = DataService.reindex(current_data)
                DataService.save_data(reindexed_data, data_type)
            
            # Prepare import stats
            import_stats = {
                'total_rows': len(df),
                'imported': len(new_entries),
                'skipped': len(skipped_entries),
                'errors': len(error_entries),
                'skipped_details': skipped_entries,
                'error_details': error_entries
            }
            
            return True, f"Imported {len(new_entries)} of {len(df)} {data_type.upper()} entries", import_stats
            
        except Exception as e:
            logger.error(f"Error importing {data_type} data: {str(e)}")
            return False, f"Error importing {data_type.upper()} data: {str(e)}", {}

    @staticmethod
    def export_training_data(data_type: Literal['ppm', 'ocm'], output_path: str = None) -> Tuple[bool, str, str]:
        """Export training data to CSV file.
        
        Args:
            data_type: Type of data to export ('ppm' or 'ocm')
            output_path: Path to save the CSV file (optional)
            
        Returns:
            Tuple of (success, message, csv_content)
        """
        try:
            # Load data
            data = DataService.load_data(data_type)
            
            if not data:
                return False, f"No {data_type.upper()} data to export", ""
            
            # Prepare data for export
            flat_data = []
            
            for entry in data:
                flat_entry = {
                    'NO': entry.get('NO'),
                    'EQUIPMENT': entry.get('EQUIPMENT'),
                    'MODEL': entry.get('MODEL'),
                    'MFG_SERIAL': entry.get('MFG_SERIAL'),
                    'MANUFACTURER': entry.get('MANUFACTURER'),
                    'LOG_NO': entry.get('LOG_NO'),
                    'PPM': entry.get('PPM', ''),
                    'OCM': entry.get('OCM', ''),
                    'machine1': entry.get('machine1', ''),
                    'machine2': entry.get('machine2', ''),
                    'machine3': entry.get('machine3', ''),
                    'machine4': entry.get('machine4', ''),
                    'machine5': entry.get('machine5', ''),
                    'machine6': entry.get('machine6', ''),
                    'machine7': entry.get('machine7', ''),
                    'machine1_trainer': entry.get('machine1_trainer', ''),
                    'machine2_trainer': entry.get('machine2_trainer', ''),
                    'machine3_trainer': entry.get('machine3_trainer', ''),
                    'machine4_trainer': entry.get('machine4_trainer', ''),
                    'machine5_trainer': entry.get('machine5_trainer', ''),
                    'machine6_trainer': entry.get('machine6_trainer', ''),
                    'machine7_trainer': entry.get('machine7_trainer', ''),
                }
                
                if data_type == 'ppm':
                    # Map quarter data
                    quarter_map = [
                        ('I', 1, 'PPM_Q_I'),
                        ('II', 2, 'PPM_Q_II'),
                        ('III', 3, 'PPM_Q_III'),
                        ('IV', 4, 'PPM_Q_IV')
                    ]
                    
                    for roman, num, q_key in quarter_map:
                        q_data = entry.get(q_key, {})
                        flat_entry[f'PPM Q {roman}'] = q_data.get('date', '')
                        flat_entry[f'Q{num}_ENGINEER'] = q_data.get('engineer', '')
                elif data_type == 'ocm':
                    flat_entry['OCM_2024'] = entry.get('OCM_2024', '')
                    flat_entry['ENGINEER'] = entry.get('ENGINEER', '')
                    flat_entry['OCM_2025'] = entry.get('OCM_2025', '')
                
                flat_data.append(flat_entry)
            
            # Define column order
            if data_type == 'ppm':
                columns_order = [
                    'NO', 'EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'PPM', 'OCM',
                    'PPM Q I', 'Q1_ENGINEER',
                    'PPM Q II', 'Q2_ENGINEER',
                    'PPM Q III', 'Q3_ENGINEER',
                    'PPM Q IV', 'Q4_ENGINEER',
                    'machine1', 'machine2', 'machine3', 'machine4', 'machine5', 'machine6', 'machine7',
                    'machine1_trainer', 'machine2_trainer', 'machine3_trainer', 'machine4_trainer', 'machine5_trainer', 'machine6_trainer', 'machine7_trainer'
                ]
            else:  # OCM
                columns_order = [
                    'NO', 'EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'PPM', 'OCM',
                    'OCM_2024', 'ENGINEER', 'OCM_2025',
                    'machine1', 'machine2', 'machine3', 'machine4', 'machine5', 'machine6', 'machine7',
                    'machine1_trainer', 'machine2_trainer', 'machine3_trainer', 'machine4_trainer', 'machine5_trainer', 'machine6_trainer', 'machine7_trainer'
                ]
            
            # Create DataFrame and export
            df = pd.DataFrame(flat_data)
            
            # Ensure all columns exist
            for col in columns_order:
                if col not in df.columns:
                    df[col] = ''
            
            # Reorder columns
            df = df[columns_order]
            
            # Export to CSV
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            if output_path:
                df.to_csv(output_path, index=False)
                return True, f"Exported {len(data)} {data_type.upper()} entries to {output_path}", csv_content
            else:
                return True, f"Exported {len(data)} {data_type.upper()} entries", csv_content
                
        except Exception as e:
            logger.error(f"Error exporting {data_type} data: {str(e)}")
            return False, f"Error exporting {data_type.upper()} data: {str(e)}", ""

    @staticmethod
    def import_training_data(data_type: Literal['ppm', 'ocm'], file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Import training data from CSV file.
        
        Args:
            data_type: Type of data to import ('ppm' or 'ocm')
            file_path: Path to CSV file
            
        Returns:
            Tuple of (success, message, import_stats)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}", {}
            
            # Load current data
            current_data = DataService.load_data(data_type)
            
            # Read CSV
            df = pd.read_csv(file_path)
            df.fillna('', inplace=True)
            
            # Drop NO column if present
            if 'NO' in df.columns:
                df = df.drop(columns=['NO'])
            
            # Convert all columns to string
            df = df.astype(str)
            
            # Process rows
            new_entries = []
            skipped_entries = []
            error_entries = []
            
            for idx, row in df.iterrows():
                row_dict = row.to_dict()
                
                try:
                    if data_type == 'ppm':
                        # Process PPM entry
                        ppm_mapping = {
                            'I': ('PPM Q I', 'Q1_ENGINEER'),
                            'II': ('PPM Q II', 'Q2_ENGINEER'),
                            'III': ('PPM Q III', 'Q3_ENGINEER'),
                            'IV': ('PPM Q IV', 'Q4_ENGINEER'),
                        }
                        
                        combined = {}
                        quarters_valid = True
                        
                        for q_key, (date_col, eng_col) in ppm_mapping.items():
                            date_val = row_dict.get(date_col, '').strip()
                            eng_val = row_dict.get(eng_col, '').strip()
                            
                            # If date is empty, mark this entry for skipping
                            if not date_val:
                                quarters_valid = False
                                break
                            
                            combined[f'PPM_Q_{q_key}'] = {
                                'date': date_val,
                                'engineer': eng_val or 'Not Assigned'  # Default engineer if empty
                            }
                        
                        if not quarters_valid:
                            skipped_entries.append(f"Row {idx+2}: Missing quarter date(s)")
                            continue
                        
                        # Process required fields
                        required_fields = ['EQUIPMENT', 'MODEL', 'MFG_SERIAL', 'MANUFACTURER', 'LOG_NO', 'PPM']
                        fields_valid = True
                        
                        for field in required_fields:
                            value = row_dict.get(field, '')
                            if not str(value).strip():
                                fields_valid = False
                                skipped_entries.append(f"Row {idx+2}: Missing required field '{field}'")
                                break
                        
                        if not fields_valid:
                            continue
                        
                        # Map the rest of the fields
                        combined.update({
                            'EQUIPMENT': row_dict['EQUIPMENT'].strip(),
                            'MODEL': row_dict['MODEL'].strip(),
                            'MFG_SERIAL': row_dict['MFG_SERIAL'].strip(),
                            'MANUFACTURER': row_dict['MANUFACTURER'].strip(),
                            'LOG_NO': str(row_dict['LOG_NO']).strip(),
                            'PPM': row_dict['PPM'].strip(),
                            'OCM': row_dict.get('OCM', '').strip(),
                            'machine1': row_dict.get('machine1', ''),
                            'machine2': row_dict.get('machine2', ''),
                            'machine3': row_dict.get('machine3', ''),
                            'machine4': row_dict.get('machine4', ''),
                            'machine5': row_dict.get('machine5', ''),
                            'machine6': row_dict.get('machine6', ''),
                            'machine7': row_dict.get('machine7', ''),
                            'machine1_trainer': row_dict.get('machine1_trainer', ''),
                            'machine2_trainer': row_dict.get('machine2_trainer', ''),
                            'machine3_trainer': row_dict.get('machine3_trainer', ''),
                            'machine4_trainer': row_dict.get('machine4_trainer', ''),
                            'machine5_trainer': row_dict.get('machine5_trainer', ''),
                            'machine6_trainer': row_dict.get('machine6_trainer', ''),
                            'machine7_trainer': row_dict.get('machine7_trainer', ''),
                        })
                        
                        # Normalize PPM value
                        if combined['PPM'].lower() == 'yes':
                            combined['PPM'] = 'Yes'
                        elif combined['PPM'].lower() == 'no':
                            combined['PPM'] = 'No'
                        else:
                            skipped_entries.append(f"Row {idx+2}: Invalid PPM value '{combined['PPM']}'")
                            continue
                        
                        # Validate using Pydantic model
                        entry = PPMEntry(**combined).model_dump()
                        
                    else:  # OCM
                        # Process OCM entry
                        combined = {
                            'EQUIPMENT': row_dict['EQUIPMENT'].strip(),
                            'MODEL': row_dict['MODEL'].strip(),
                            'MFG_SERIAL': row_dict['MFG_SERIAL'].strip(),
                            'MANUFACTURER': row_dict['MANUFACTURER'].strip(),
                            'LOG_NO': str(row_dict['LOG_NO']).strip(),
                            'PPM': row_dict.get('PPM', '').strip(),
                            'OCM': row_dict['OCM'].strip(),
                            'OCM_2024': row_dict.get('OCM_2024', '').strip(),
                            'ENGINEER': row_dict.get('ENGINEER', '').strip(),
                            'OCM_2025': row_dict.get('OCM_2025', '').strip(),
                            'machine1': row_dict.get('machine1', ''),
                            'machine2': row_dict.get('machine2', ''),
                            'machine3': row_dict.get('machine3', ''),
                            'machine4': row_dict.get('machine4', ''),
                            'machine5': row_dict.get('machine5', ''),
                            'machine6': row_dict.get('machine6', ''),
                            'machine7': row_dict.get('machine7', ''),
                            'machine1_trainer': row_dict.get('machine1_trainer', ''),
                            'machine2_trainer': row_dict.get('machine2_trainer', ''),
                            'machine3_trainer': row_dict.get('machine3_trainer', ''),
                            'machine4_trainer': row_dict.get('machine4_trainer', ''),
                            'machine5_trainer': row_dict.get('machine5_trainer', ''),
                            'machine6_trainer': row_dict.get('machine6_trainer', ''),
                            'machine7_trainer': row_dict.get('machine7_trainer', ''),
                        }
                        
                        # Normalize OCM value
                        if combined['OCM'].lower() == 'yes':
                            combined['OCM'] = 'Yes'
                        elif combined['OCM'].lower() == 'no':
                            combined['OCM'] = 'No'
                        else:
                            skipped_entries.append(f"Row {idx+2}: Invalid OCM value '{combined['OCM']}'")
                            continue
                        
                        # Validate using Pydantic model
                        entry = OCMEntry(**combined).model_dump()
                    
                    # Check for duplicate MFG_SERIAL in existing data and new entries
                    mfg_serial = entry['MFG_SERIAL']
                    is_duplicate = False
                    
                    for existing_entry in current_data:
                        if existing_entry['MFG_SERIAL'] == mfg_serial:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        for new_entry in new_entries:
                            if new_entry['MFG_SERIAL'] == mfg_serial:
                                is_duplicate = True
                                break
                    
                    if is_duplicate:
                        skipped_entries.append(f"Row {idx+2}: Duplicate MFG_SERIAL '{mfg_serial}'")
                        continue
                    
                    # Add to new entries
                    new_entries.append(entry)
                    
                except ValidationError as e:
                    error_entries.append(f"Row {idx+2}: Validation error - {str(e)}")
                except Exception as e:
                    error_entries.append(f"Row {idx+2}: Unexpected error - {str(e)}")
            
            # If any entries were processed, add them to the current data and save
            if new_entries:
                current_data.extend(new_entries)
                reindexed_data = DataService.reindex(current_data)
                DataService.save_data(reindexed_data, data_type)
            
            # Prepare import stats
            import_stats = {
                'total_rows': len(df),
                'imported': len(new_entries),
                'skipped': len(skipped_entries),
                'errors': len(error_entries),
                'skipped_details': skipped_entries,
                'error_details': error_entries
            }
            
            return True, f"Imported {len(new_entries)} of {len(df)} {data_type.upper()} entries", import_stats
            
        except Exception as e:
            logger.error(f"Error importing {data_type} data: {str(e)}")
            return False, f"Error importing {data_type.upper()} data: {str(e)}", {}
