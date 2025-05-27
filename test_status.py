#!/usr/bin/env python3
"""
Test script for status calculation functionality
"""
import sys
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.routes.views_new import calculate_equipment_status

def test_ppm_status():
    """Test PPM status calculation"""
    print("Testing PPM status calculation...")
    
    # Test case 1: Overdue PPM
    today = datetime.now()
    overdue_date = (today - timedelta(days=10)).strftime('%d/%m/%Y')
    ppm_entry_overdue = {
        'PPM_Q_I': {'date': overdue_date},
        'status_override': None
    }
    result = calculate_equipment_status(ppm_entry_overdue, 'ppm')
    print(f"Overdue PPM: {result}")
    assert result['status'] == 'Overdue'
    assert result['class'] == 'danger'
    
    # Test case 2: Due Soon PPM
    due_soon_date = (today + timedelta(days=5)).strftime('%d/%m/%Y')
    ppm_entry_due_soon = {
        'PPM_Q_I': {'date': due_soon_date},
        'status_override': None
    }
    result = calculate_equipment_status(ppm_entry_due_soon, 'ppm')
    print(f"Due Soon PPM: {result}")
    assert result['status'] == 'Due Soon'
    assert result['class'] == 'warning'
    
    # Test case 3: OK PPM
    ok_date = (today + timedelta(days=30)).strftime('%d/%m/%Y')
    ppm_entry_ok = {
        'PPM_Q_I': {'date': ok_date},
        'status_override': None
    }
    result = calculate_equipment_status(ppm_entry_ok, 'ppm')
    print(f"OK PPM: {result}")
    assert result['status'] == 'OK'
    assert result['class'] == 'success'
    
    # Test case 4: Status override
    ppm_entry_override = {
        'PPM_Q_I': {'date': ok_date},
        'status_override': 'Overdue'
    }
    result = calculate_equipment_status(ppm_entry_override, 'ppm')
    print(f"Override PPM: {result}")
    assert result['status'] == 'Overdue'
    assert result['class'] == 'danger'
    
    print("PPM tests passed!")

def test_ocm_status():
    """Test OCM status calculation"""
    print("\nTesting OCM status calculation...")
    
    # Test case 1: Overdue OCM
    today = datetime.now()
    overdue_date = (today - timedelta(days=10)).strftime('%d/%m/%Y')
    ocm_entry_overdue = {
        'Next_Date': overdue_date,
        'status_override': None
    }
    result = calculate_equipment_status(ocm_entry_overdue, 'ocm')
    print(f"Overdue OCM: {result}")
    assert result['status'] == 'Overdue'
    assert result['class'] == 'danger'
    
    # Test case 2: Due Soon OCM
    due_soon_date = (today + timedelta(days=5)).strftime('%d/%m/%Y')
    ocm_entry_due_soon = {
        'Next_Date': due_soon_date,
        'status_override': None
    }
    result = calculate_equipment_status(ocm_entry_due_soon, 'ocm')
    print(f"Due Soon OCM: {result}")
    assert result['status'] == 'Due Soon'
    assert result['class'] == 'warning'
    
    # Test case 3: OK OCM
    ok_date = (today + timedelta(days=30)).strftime('%d/%m/%Y')
    ocm_entry_ok = {
        'Next_Date': ok_date,
        'status_override': None
    }
    result = calculate_equipment_status(ocm_entry_ok, 'ocm')
    print(f"OK OCM: {result}")
    assert result['status'] == 'OK'
    assert result['class'] == 'success'
    
    print("OCM tests passed!")

if __name__ == '__main__':
    try:
        test_ppm_status()
        test_ocm_status()
        print("\n✅ All tests passed! Status calculation is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1) 