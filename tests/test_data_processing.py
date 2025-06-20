import pandas as pd
import pytest
import os
import tempfile
from datetime import datetime, timedelta
from src.utils.data_processing import load_subs, save_subs, infer_week_range, generate_preview

def test_load_save_subs():
    """Test loading and saving the subcontractors list."""
    # Create a temporary file for testing
    temp_file = "test_subs.txt"
    
    try:
        # Test save function
        test_subs = "Test Sub 1\nTest Sub 2\nTest Sub 3"
        
        # Override default subs file path for testing
        import src.utils.data_processing
        original_subs_file = src.utils.data_processing.SUBS_FILE
        src.utils.data_processing.SUBS_FILE = temp_file
        
        # Test save
        save_subs(test_subs)
        
        # Test load
        loaded_subs = load_subs()
        
        # Verify content
        assert len(loaded_subs) == 3
        assert "Test Sub 1" in loaded_subs
        assert "Test Sub 2" in loaded_subs
        assert "Test Sub 3" in loaded_subs
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        # Restore original path
        src.utils.data_processing.SUBS_FILE = original_subs_file

def test_infer_week_range():
    """Test the week range inference from dates."""
    # Create a test DataFrame with dates
    today = datetime.now().date()
    
    # Find the current week's Monday and Sunday
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    # Create some sample data
    data = {
        'Tech': ['Tech 1', 'Tech 2', 'Tech 3', 'Tech 4'],
        'Job#': ['1001', '1002', '1003', '1004'],
        'Completed On': [monday, monday + timedelta(days=2), sunday, None],
        'Job Category': ['Category 1', 'Category 2', 'Category 3', 'Category 4']
    }
    
    df = pd.DataFrame(data)
    
    # Test inference
    start, end = infer_week_range(df)
    
    # Verify results
    assert start == monday
    assert end == sunday

def test_generate_preview():
    """Test filtering jobs based on criteria."""
    # Create a test DataFrame
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    data = {
        'Tech': ['Sub 1', 'Sub 2', 'Sub 1', 'Sub 3', 'Totals represent tech\'s share'],
        'Job#': ['1001', '1002', '1003', '1004', '1005'],
        'Completed On': [monday, monday + timedelta(days=2), sunday, None, monday],
        'Job Category': ['Category 1', 'Category 2', 'Category 3', 'Category 4', 'Category 5']
    }
    
    df = pd.DataFrame(data)
    
    # Test filtering with all subcontractors
    filtered_df, warnings = generate_preview(df, ['Sub 1', 'Sub 2', 'Sub 3'], [monday, sunday])
    
    # Verify results
    assert len(filtered_df) == 4  # Should exclude the 'Totals' row
    assert filtered_df['Missing Date'].sum() == 1  # One row has missing date
    
    # Test filtering with limited subcontractors
    filtered_df, warnings = generate_preview(df, ['Sub 1'], [monday, sunday])
    
    # Verify results
    assert len(filtered_df) == 2  # Only Sub 1 rows
    assert all(filtered_df['Tech'] == 'Sub 1')

if __name__ == "__main__":
    pytest.main(['-v', __file__]) 