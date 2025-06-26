from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
import aiosqlite
import csv
import io
import zipfile
from config import config
from auth import get_current_user
from typing import Dict, List

router = APIRouter()

# CRM field mappings
CRM_MAPPINGS = {
    "salesforce": {
        "email": "Email",
        "first_name": "FirstName", 
        "last_name": "LastName",
        "company": "Company",
        "title": "Title",
        "phone": "Phone"
    },
    "hubspot": {
        "email": "Email",
        "first_name": "First Name",
        "last_name": "Last Name", 
        "company": "Company Name",
        "title": "Job Title",
        "phone": "Phone Number"
    },
    "pipedrive": {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "company": "org_name", 
        "title": "title",
        "phone": "phone"
    }
}

def get_sample_data() -> List[Dict]:
    """Generate sample CRM data based on decoy information"""
    return [
        {
            "email": "john.doe@acumenpulse.com",
            "first_name": "John",
            "last_name": "Doe", 
            "company": "Acumen Pulse",
            "title": "CEO",
            "phone": "+1-555-0123"
        },
        {
            "email": "sarah.smith@techcorp.com",
            "first_name": "Sarah",
            "last_name": "Smith",
            "company": "TechCorp", 
            "title": "VP Sales",
            "phone": "+1-555-0456"
        }
    ]

def create_csv_content(data: List[Dict], crm_type: str) -> str:
    """Create CSV content with CRM-specific field mappings"""
    if crm_type not in CRM_MAPPINGS:
        raise HTTPException(status_code=400, detail=f"Unsupported CRM type: {crm_type}")
    
    mapping = CRM_MAPPINGS[crm_type]
    output = io.StringIO()
    
    if data:
        # Use CRM-specific headers
        headers = list(mapping.values())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        for row in data:
            mapped_row = {}
            for standard_field, crm_field in mapping.items():
                mapped_row[crm_field] = row.get(standard_field, "")
            writer.writerow(mapped_row)
    
    return output.getvalue()

def create_instructions(crm_type: str) -> str:
    """Create instruction file for CRM upload"""
    instructions = {
        "salesforce": """Salesforce Import Instructions:

1. Log into your Salesforce account
2. Go to Setup > Data > Data Import Wizard
3. Choose 'Contacts' as the object to import
4. Upload the CSV file provided
5. Map the fields if needed (they should auto-match)
6. Review and start the import

Note: Ensure you have proper permissions to import contacts.""",

        "hubspot": """HubSpot Import Instructions:

1. Log into your HubSpot account
2. Go to Contacts > Import
3. Choose 'File from computer'
4. Upload the CSV file provided
5. Map the properties (they should auto-match)
6. Review and start the import

Note: Ensure you have Marketing or Sales Hub access.""",

        "pipedrive": """Pipedrive Import Instructions:

1. Log into your Pipedrive account
2. Go to Contacts > Import data
3. Upload the CSV file provided
4. Map the fields (they should auto-match)
5. Review and start the import

Note: Ensure you have admin permissions to import data."""
    }
    
    return instructions.get(crm_type, "Generic CRM import instructions not available.")

@router.get("/api/export")
async def export_data(crm: str = Query(..., description="CRM type (salesforce, hubspot, pipedrive)"), current_user: str = Depends(get_current_user)):
    """Export data in CRM-specific format as a downloadable ZIP file"""
    
    if crm not in CRM_MAPPINGS:
        raise HTTPException(status_code=400, detail=f"Unsupported CRM type: {crm}")
    
    # Get sample data (in real implementation, fetch from database)
    data = get_sample_data()
    
    # Create CSV content
    csv_content = create_csv_content(data, crm)
    
    # Create instructions
    instructions = create_instructions(crm)
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add CSV file
        zip_file.writestr(f"{crm}_contacts.csv", csv_content)
        # Add instructions
        zip_file.writestr("import_instructions.txt", instructions)
    
    zip_buffer.seek(0)
    
    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={crm}_export.zip"}
    )