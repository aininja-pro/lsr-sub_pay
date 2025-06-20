# Subcontractor Pay Sheet Generator

A Streamlit web application that automates the weekly creation of subcontractor pay sheets from Service Fusion reports.

## Overview

This application simplifies the process of creating subcontractor pay sheets by:

1. Reading Service Fusion reports (Excel format)
2. Filtering jobs by approved subcontractors and date range
3. Populating pay sheet templates with the filtered jobs
4. Preserving all template formatting, headers, and formulas
5. Providing a downloadable Excel file with the completed pay sheets

## Features

- **File Upload**: Upload Service Fusion report and pay sheet template
- **Subcontractor Management**: Edit and save the approved subcontractor list
- **Date Selection**: Automatic or manual selection of the Monday-Sunday date range
- **Job Preview**: View filtered jobs grouped by subcontractor before generating pay sheets
- **Template Validation**: Warning messages for missing subcontractor tabs
- **Download**: One-click download of the final pay sheet workbook

## Installation

### Local Development

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   streamlit run src/app.py
   ```

### Deployment

The application is deployable on Streamlit Cloud:

1. Connect your GitHub repository to Streamlit Cloud
2. Set Python version to 3.11+
3. Deploy the application

## Usage

1. **Prepare Files**:
   - Export Service Fusion report as Excel (.xlsx) with "Worksheet" sheet
   - Prepare pay sheet template with one tab per subcontractor

2. **Upload Files**:
   - Upload both files in the main area of the application

3. **Configure Settings**:
   - Edit subcontractor list in the sidebar if needed
   - Review or adjust the date range

4. **Generate Preview**:
   - Click "Generate Preview" to see filtered jobs
   - Review jobs grouped by subcontractor

5. **Generate Pay Sheet**:
   - Click "Generate Pay Sheet" to process the data
   - Download the resulting Excel file

## Structure

The application follows this structure:

```
.
├── src/
│   ├── app.py                # Main Streamlit application
│   └── utils/
│       ├── data_processing.py # Data filtering and processing
│       └── excel_writer.py    # Template population and Excel generation
├── tests/                    # Unit tests
├── requirements.txt          # Dependencies
└── subcontractors.txt        # Persistent subcontractor list
```

## Development

### Running Tests

```
pytest tests/
```

### Adding New Features

1. Modify data processing in `src/utils/data_processing.py`
2. Update Excel generation in `src/utils/excel_writer.py`
3. Adjust UI components in `src/app.py` 