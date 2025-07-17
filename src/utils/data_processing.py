import pandas as pd
import os
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default list of subcontractors (fallback if file is missing or empty)
DEFAULT_SUBS = [
    "Fire Sprinkler Co.",
    "HVAC Masters",
    "Electric Pros"
]

# Path to the subcontractors text files
# Use a more robust path approach
CONSTRUCTION_SUBS_FILE = Path(os.path.abspath("subcontractors.txt"))
WELDING_SUBS_FILE = Path(os.path.abspath("welding_subcontractors.txt"))

@st.cache_data
def load_subs(team="Construction"):
    """
    Load the subcontractor list from the text file for the specified team.
    Falls back to default list if file is missing or empty.
    
    Args:
        team (str): Team name ("Construction" or "Welding")
    
    Returns:
        list: List of subcontractor names
    """
    try:
        subs_file_path = CONSTRUCTION_SUBS_FILE if team == "Construction" else WELDING_SUBS_FILE
        logger.info(f"Trying to load {team} subcontractors from: {subs_file_path}")
        
        if not subs_file_path.exists():
            logger.info(f"Subcontractor file not found at {subs_file_path}. Using default list.")
            return DEFAULT_SUBS
        
        with open(subs_file_path, 'r') as f:
            lines = f.read().splitlines()
        
        # Filter out empty lines and strip whitespace
        subs = [line.strip() for line in lines if line.strip()]
        
        if not subs:
            logger.info(f"Subcontractor file is empty. Using default list.")
            return DEFAULT_SUBS
            
        logger.info(f"Loaded {len(subs)} subcontractors from file: {subs}")
        return subs
    
    except Exception as e:
        logger.error(f"Error loading subcontractors: {str(e)}")
        return DEFAULT_SUBS

def save_subs(text, team="Construction"):
    """
    Save the subcontractor list to the text file for the specified team.
    
    Args:
        text (str): Text content with one subcontractor per line
        team (str): Team name ("Construction" or "Welding")
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Split the text by newlines and filter out empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Get absolute path
        subs_file_path = CONSTRUCTION_SUBS_FILE if team == "Construction" else WELDING_SUBS_FILE
        logger.info(f"Saving {team} subcontractors to: {subs_file_path}")
        
        # Write to file
        with open(subs_file_path, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Saved {len(lines)} subcontractors to file: {lines}")
        
        # Clear the load_subs cache so it reloads on next call
        load_subs.clear()
        
        return True
    
    except Exception as e:
        logger.error(f"Error saving subcontractors: {str(e)}")
        return False

def infer_week_range(df):
    """
    Infer the Monday-Sunday date range based on the 'Completed On' dates in the report.
    
    Args:
        df (pandas.DataFrame): Service Fusion report DataFrame
    
    Returns:
        tuple: (start_date, end_date) as datetime.date objects
    """
    try:
        # Ensure 'Completed On' column exists
        if 'Completed On' not in df.columns:
            logger.error("'Completed On' column not found in report.")
            # Return current week's Monday and Sunday as fallback
            today = datetime.now().date()
            start = today - timedelta(days=today.weekday())  # Monday
            end = start + timedelta(days=6)  # Sunday
            return start, end
        
        # Convert to datetime, handling potential errors
        df['Completed On'] = pd.to_datetime(df['Completed On'], errors='coerce')
        
        # Drop rows with missing dates for the purpose of inference
        dates_df = df.dropna(subset=['Completed On'])
        
        if dates_df.empty:
            logger.warning("No valid dates found in 'Completed On' column.")
            # Return current week's Monday and Sunday as fallback
            today = datetime.now().date()
            start = today - timedelta(days=today.weekday())  # Monday
            end = start + timedelta(days=6)  # Sunday
            return start, end
        
        # Get min and max dates
        min_date = dates_df['Completed On'].min().date()
        max_date = dates_df['Completed On'].max().date()
        
        # Find the Monday of the week containing the min date
        start_date = min_date - timedelta(days=min_date.weekday())
        
        # Find the Sunday of the week containing the max date
        end_date = max_date + timedelta(days=(6 - max_date.weekday()))
        
        # If the range is more than 14 days, limit to the most recent week
        if (end_date - start_date).days > 14:
            logger.info(f"Date range too wide ({(end_date - start_date).days} days). Limiting to the most recent week.")
            end_date = max_date + timedelta(days=(6 - max_date.weekday()))
            start_date = end_date - timedelta(days=6)
        
        logger.info(f"Inferred date range: {start_date} to {end_date}")
        return start_date, end_date
    
    except Exception as e:
        logger.error(f"Error inferring date range: {str(e)}")
        # Return current week's Monday and Sunday as fallback
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())  # Monday
        end = start + timedelta(days=6)  # Sunday
        return start, end

def generate_preview(df, subs_list, date_range):
    """
    Filter the report based on subcontractor list and Invoiced status only.
    Ensures we keep the property address and job details columns for the pay sheet.
    
    Args:
        df (pandas.DataFrame): Service Fusion report DataFrame
        subs_list (list): List of approved subcontractor names
        date_range (list): Not used for filtering
    
    Returns:
        tuple: (filtered_df, warnings) - DataFrame of filtered jobs and list of warning messages
    """
    warnings = []
    
    try:
        # Make a copy to avoid modifying the original
        filtered_df = df.copy()
        original_count = len(filtered_df)
        logger.info(f"Starting with {original_count} total rows")
        
        # Print column names for debugging
        logger.info(f"Columns in the DataFrame: {list(filtered_df.columns)}")
        
        # Check for important columns used for the pay sheet
        important_cols = ['Tech', 'Job#', 'Job Category', 'Service Location Address 1', 'Job Details', 'Customer', 'Customer)', 'Customer )']
        available_cols = list(filtered_df.columns)
        missing_important = [col for col in important_cols if col not in available_cols]
        
        # Check specifically for Customer column variations
        customer_cols_found = [col for col in ['Customer', 'Customer)', 'Customer )'] if col in available_cols]
        
        if customer_cols_found:
            logger.info(f"Found Customer column variations: {customer_cols_found}")
        else:
            logger.warning(f"No Customer column found! Available columns: {available_cols}")
            warnings.append("Customer column not found in the report. Property field will use Service Location Address as fallback.")
        
        if missing_important:
            logger.warning(f"Some important columns are missing that may be needed for the pay sheet: {missing_important}")
            # Only warn about truly missing columns (exclude Customer variations if at least one is found)
            truly_missing = [col for col in missing_important if not (col.startswith('Customer') and customer_cols_found)]
            if truly_missing:
                warnings.append(f"Missing columns needed for pay sheet: {', '.join(truly_missing)}. Output may be incomplete.")

        # Convert Tech column to string to handle potential numeric values
        filtered_df['Tech'] = filtered_df['Tech'].astype(str)
        
        # Filter out rows with "Totals represent tech's share" in the Tech column
        totals_mask = filtered_df['Tech'].str.contains("Totals represent tech's share", na=False, case=False)
        filtered_df = filtered_df[~totals_mask]
        non_totals_count = len(filtered_df)
        logger.info(f"After removing 'Totals' rows: {non_totals_count} rows (removed {original_count - non_totals_count})")
        
        # Add debug info - what are all the unique tech names?
        unique_techs = filtered_df['Tech'].unique()
        logger.info(f"All unique Tech names in data: {list(unique_techs)}")
        
        # Log subcontractor list we're checking against
        logger.info(f"Filtering for subcontractors: {subs_list}")
        
        # Filter by subcontractor list (case-insensitive)
        subs_lower = [sub.lower().strip() for sub in subs_list]
        subs_mask = filtered_df['Tech'].str.lower().str.strip().isin(subs_lower)
        filtered_df = filtered_df[subs_mask]
        sub_filtered_count = len(filtered_df)
        logger.info(f"After filtering for selected subcontractors: {sub_filtered_count} rows (removed {non_totals_count - sub_filtered_count})")
        
        if filtered_df.empty:
            msg = "No jobs match the selected subcontractors."
            logger.warning(msg)
            warnings.append(msg)
            return filtered_df, warnings
        
        # Debug - what's in filtered_df BEFORE status filter?
        for idx, row in filtered_df.iterrows():
            logger.info(f"Row {idx}: Tech={row['Tech']}, Job#={row['Job#']}, Status={row.get('Status', 'N/A')}, Completed On={row.get('Completed On', 'N/A')}")
        
        # Filter for rows where Status is "Invoiced" if the column exists
        if 'Status' in filtered_df.columns:
            # Log all unique status values
            unique_statuses = filtered_df['Status'].unique()
            logger.info(f"All unique Status values: {list(unique_statuses)}")
            
            invoiced_mask = filtered_df['Status'] == 'Invoiced'
            filtered_df = filtered_df[invoiced_mask]
            invoiced_count = len(filtered_df)
            logger.info(f"After filtering for 'Invoiced' status: {invoiced_count} rows (removed {sub_filtered_count - invoiced_count})")
        
        # Set Missing Date flag to False for all rows (no date filtering)
        filtered_df['Missing Date'] = False
        
        if filtered_df.empty:
            msg = "No jobs match the criteria (subcontractor and Invoiced status)."
            logger.warning(msg)
            warnings.append(msg)
        else:
            # Log the FINAL results
            logger.info(f"Final result: {len(filtered_df)} jobs")
            for idx, row in filtered_df.head(20).iterrows():
                logger.info(f"Final row {idx}: Tech={row['Tech']}, Job#={row['Job#']}, Status={row.get('Status', 'N/A')}, Completed On={row.get('Completed On', 'N/A')}")
        
        return filtered_df, warnings
    
    except Exception as e:
        msg = f"Error generating preview: {str(e)}"
        logger.error(msg)
        warnings.append(msg)
        return pd.DataFrame(), warnings 