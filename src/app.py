import streamlit as st
import pandas as pd
import os
from utils.data_processing import load_subs, save_subs, infer_week_range, generate_preview
from utils.excel_writer import create_pay_sheet

# Set page title and configuration
st.set_page_config(
    page_title="Subcontractor Pay Sheet Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App header
st.title("Subcontractor Pay Sheet Generator")
st.write("Upload your Service Fusion report and pay sheet template to generate pay sheets for your subcontractors.")

# Initialize session state variables if they don't exist
if 'subs_list' not in st.session_state:
    st.session_state.subs_list = []
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None
if 'filtered_jobs' not in st.session_state:
    st.session_state.filtered_jobs = None
if 'selected_team' not in st.session_state:
    st.session_state.selected_team = 'Construction'

# Sidebar - Subcontractor List Management
with st.sidebar:
    st.header("Settings")
    
    # Team selection
    st.subheader("Team Selection")
    team = st.selectbox(
        "Select Team",
        ["Construction", "Welding"],
        index=0 if st.session_state.selected_team == 'Construction' else 1,
        help="Choose between Construction and Welding teams"
    )
    
    # Update selected team in session state
    if team != st.session_state.selected_team:
        st.session_state.selected_team = team
        st.rerun()
    
    # Subcontractor list management
    st.subheader(f"{team} Subcontractor List")
    subs_text = st.text_area("Edit subcontractor names (one per line)", value="\n".join(load_subs(team)), height=200)
    
    if st.button("Save List"):
        save_subs(subs_text, team)
        st.success(f"{team} subcontractor list saved!")
    
    # Date range selection
    st.subheader("Date Range")
    
    # If a report is loaded and dates are available, use them for the input
    if st.session_state.start_date and st.session_state.end_date:
        date_range = st.date_input(
            "Select Week (Monday-Sunday)",
            [st.session_state.start_date, st.session_state.end_date],
            help="Automatically set to the Monday-Sunday of the report's dates. Can be manually adjusted."
        )
    else:
        date_range = st.date_input(
            "Select Week (Monday-Sunday)",
            [],
            help="Will be automatically set once a report is uploaded."
        )
    
    # If date range is selected, update session state
    if len(date_range) == 2:
        st.session_state.start_date = date_range[0]
        st.session_state.end_date = date_range[1]

# Main area - File Upload
col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload Service Fusion Report")
    report_file = st.file_uploader("Upload Service Fusion Excel report (.xlsx)", type="xlsx", help="The report should contain a sheet named 'Worksheet'")

with col2:
    st.subheader("Upload Pay Sheet Template")
    template_file = st.file_uploader("Upload Pay Sheet Template (.xlsx)", type="xlsx", help="Template should have one sheet per subcontractor")

# Process files when both are uploaded
if report_file and template_file:
    try:
        # Load the report and infer date range if not already set
        report_df = pd.read_excel(report_file, sheet_name="Worksheet")
        
        # Infer date range if not set
        if not st.session_state.start_date or not st.session_state.end_date:
            st.session_state.start_date, st.session_state.end_date = infer_week_range(report_df)
            st.sidebar.success("Date range automatically set based on report dates.")
            # Need to rerun to update the date input widget
            st.rerun()
        
        # Get updated subcontractor list for selected team
        subs_list = load_subs(st.session_state.selected_team)
        
        # Preview Generation Button
        if st.button("Generate Preview", type="primary"):
            with st.spinner("Filtering jobs..."):
                # Generate preview DataFrame
                preview_df, warnings = generate_preview(
                    report_df, 
                    subs_list, 
                    [st.session_state.start_date, st.session_state.end_date]
                )
                
                # Store in session state
                st.session_state.filtered_jobs = preview_df
                
                # Display warnings if any
                if warnings:
                    st.warning("\n".join(warnings))
                
                # Show preview in an expander
                with st.expander("Job Preview", expanded=True):
                    if preview_df.empty:
                        st.warning("No jobs found matching the criteria.")
                    else:
                        # Group by subcontractor for better viewing
                        for sub, group in preview_df.groupby('Tech'):
                            st.subheader(f"{sub} ({len(group)} jobs)")
                            st.dataframe(
                                group[['Job#', 'Completed On', 'Job Category']],
                                hide_index=True,
                                use_container_width=True
                            )
        
        # Only show Generate Pay Sheet button if we have a preview
        if st.session_state.filtered_jobs is not None:
            if st.button("Generate Pay Sheet", type="primary"):
                with st.spinner("Creating pay sheet..."):
                    # Generate the pay sheet
                    output_path, skipped_subs = create_pay_sheet(
                        template_file,
                        st.session_state.filtered_jobs,
                        [st.session_state.start_date, st.session_state.end_date]
                    )
                    
                    # Show warnings for skipped subcontractors
                    if skipped_subs:
                        st.warning(f"The following subcontractors were skipped because they don't have matching tabs in the template: {', '.join(skipped_subs)}")
                    
                    # Provide download button
                    with open(output_path, "rb") as file:
                        st.download_button(
                            label="Download Pay Sheet",
                            data=file,
                            file_name=os.path.basename(output_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
    
    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
else:
    st.info("Please upload both the Service Fusion report and the pay sheet template to proceed.") 