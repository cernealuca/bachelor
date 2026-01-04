"""
Manual Field Extraction Template
For extracting field names from PDF Table of Contents
"""

# Template CSV structure for manual extraction
csv_template = """Field Name,Zone/Platform,Page Number,Notes
Moreni,Pre-Carpathian,45,Historic field
Câmpina,Pre-Carpathian,67,
Bordei Verde,Moesian Platform,123,Major field
"""

# Instructions for manual extraction
instructions = """
MANUAL FIELD EXTRACTION GUIDE
==============================

STEP 1: Open the PDF
--------------------
Open: c:\\cod\\licenta\\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf

STEP 2: Find Table of Contents
-------------------------------
Look in the first 10-20 pages for:
- "CUPRINS" (Contents in Romanian)
- "TABLE OF CONTENTS"
- "INDEX"
- List of field names with page numbers

STEP 3: Extract Field Data
---------------------------
For each field mentioned, write down:
1. Field name (exact spelling)
2. Geographic zone/platform (if mentioned)
3. Page number where detailed info starts
4. Any notes (production type: oil/gas, discovery year, etc.)

STEP 4: Save to CSV
--------------------
Create file: c:\\cod\\licenta\\manual_fields.csv

Format:
Field Name,Zone,Page,Notes
Example 1,Moesian Platform,45,Oil field
Example 2,Pre-Carpathian,67,Gas field

STEP 5: Tell Me When Ready
----------------------------
Once you've extracted 20-50 fields, let me know!
I'll add them to the knowledge graph.

TARGET: 50-100 major fields (most important ones first)
TIME: 1-2 hours for good coverage

TIPS:
-----
- Focus on major/large fields first
- Romanian characters: ă, â, î, ș, ț (important for accuracy!)
- If unsure about zone, just put the field name
- We can add more details later

"""

def create_extraction_template():
    """Create template files for manual extraction"""
    
    import os
    
    # Create template CSV
    template_file = r'c:\cod\licenta\manual_fields_TEMPLATE.csv'
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(csv_template)
    
    print(f"✓ Created template: {template_file}")
    
    # Create instructions file
    instructions_file = r'c:\cod\licenta\MANUAL_EXTRACTION_GUIDE.txt'
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"✓ Created guide: {instructions_file}")
    
    print(f"\n{'='*80}")
    print(f"MANUAL EXTRACTION READY")
    print(f"{'='*80}")
    print(f"\n1. Open the PDF")
    print(f"2. Find Table of Contents / Field Index")
    print(f"3. Fill in: manual_fields_TEMPLATE.csv")
    print(f"4. Save as: manual_fields.csv")
    print(f"\nRead MANUAL_EXTRACTION_GUIDE.txt for detailed instructions")


def process_manual_csv(csv_file=r'c:\cod\licenta\manual_fields.csv'):
    """Process manually created CSV file"""
    
    import csv
    from pathlib import Path
    
    if not Path(csv_file).exists():
        print(f"✗ File not found: {csv_file}")
        print(f"\nPlease create the file first using the template!")
        return None
    
    fields = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row['Field Name']:  # Skip empty rows
                fields.append({
                    'name': row['Field Name'].strip(),
                    'zone': row.get('Zone', '').strip(),
                    'page': row.get('Page Number', '').strip(),
                    'notes': row.get('Notes', '').strip()
                })
    
    print(f"\n✓ Loaded {len(fields)} fields from manual extraction!")
    
    for field in fields[:10]:  # Show first 10
        print(f"  - {field['name']}")
        if len(fields) > 10:
            print(f"  ... and {len(fields)-10} more")
    
    return fields


def main():
    """Main execution"""
    
    print("\n" + "="*80)
    print("MANUAL FIELD EXTRACTION TOOL")
    print("="*80)
    
    import sys
    
    if '--create-template' in sys.argv:
        create_extraction_template()
    
    elif '--process' in sys.argv:
        fields = process_manual_csv()
        
        if fields:
            print(f"\n📊 Ready to add {len(fields)} fields to knowledge graph!")
            print(f"\nRun: python update_knowledge_with_fields.py")
    
    else:
        print("\nUsage:")
        print("  python manual_extraction.py --create-template")
        print("    Creates template CSV and instructions")
        print()
        print("  python manual_extraction.py --process")
        print("    Processes your completed CSV file")
        print()
        create_extraction_template()


if __name__ == "__main__":
    main()
