"""
Simple approach: Extract what we can from the PDFs and manually review critical pages
Focus on building GraphRAG with available data (559 pages already extracted)
"""

from pypdf import PdfReader
import json
from pathlib import Path

def deep_text_extraction(pdf_path):
    """
    More aggressive text extraction attempt
    """
    reader = PdfReader(pdf_path)
    
    print(f"\nAnalyzing: {Path(pdf_path).name}")
    print(f"Pages: {len(reader.pages)}")
    
    extracted_pages = []
    empty_pages = 0
    
    for page_num, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text()
            
            if text and len(text.strip()) > 30:
                extracted_pages.append({
                    'page': page_num,
                    'text': text,
                    'char_count': len(text)
                })
            else:
                empty_pages += 1
                
        except Exception as e:
            empty_pages += 1
            continue
    
    print(f"✓ Extracted text from {len(extracted_pages)} pages")
    print(f"✗ {empty_pages} pages had no extractable text (likely scanned images)")
    
    return extracted_pages, empty_pages

def analyze_field_catalog():
    """
    Analyze the problematic 1979 PDF
    Since it's image-based, we'll note which pages and proceed with other documents
    """
    
    pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
    
    extracted, empty = deep_text_extraction(pdf_path)
    
    if empty > 300:  # Most pages are images
        print(f"\n⚠️  This PDF is primarily scanned images.")
        print(f"    Will need OCR or manual digitization.")
        print(f"    RECOMMENDATION: Proceed with GraphRAG using other 559 pages,")
        print(f"    then add field catalog data later when OCR is available.")
    
    return extracted

def main():
    """Quick assessment"""
    
    print("="*80)
    print("PDF EXTRACTION ASSESSMENT")
    print("="*80)
    
    # Check the problematic PDF
    catalog_pages = analyze_field_catalog()
    
    print(f"\n{'='*80}")
    print("DECISION: Proceed with GraphRAG Implementation")
    print("="*80)
    print(f"\nWe have 559 pages of good text data from 2 PDFs.")
    print(f"This is sufficient to:")
    print(f"1. Build knowledge graph of geological concepts")
    print(f"2. Extract zones, formations, and relationships") 
    print(f"3. Create AI system that understands Romanian petroleum geology")
    print(f"4. Demonstrate impressive capabilities to specialists")
    print(f"\nThe 1979 field catalog can be added later via:")
    print(f"- Better OCR tools when available")
    print(f"- Manual data entry for critical fields")
    print(f"- Supplementary online research")
    
    print(f"\n🚀 Next step: Build GraphRAG system with available data")

if __name__ == "__main__":
    main()
