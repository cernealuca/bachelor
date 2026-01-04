"""
PDF Analysis Script
Extracts metadata and sample content from the geological PDFs
"""
import os
from pypdf import PdfReader
import json

def analyze_pdf(pdf_path):
    """Extract metadata and content summary from a PDF"""
    try:
        reader = PdfReader(pdf_path)
        
        # Get metadata
        metadata = {
            'filename': os.path.basename(pdf_path),
            'num_pages': len(reader.pages),
            'file_size_mb': round(os.path.getsize(pdf_path) / (1024 * 1024), 2)
        }
        
        # Try to extract title and author from metadata
        if reader.metadata:
            metadata['title'] = reader.metadata.get('/Title', 'N/A')
            metadata['author'] = reader.metadata.get('/Author', 'N/A')
            metadata['subject'] = reader.metadata.get('/Subject', 'N/A')
            metadata['creator'] = reader.metadata.get('/Creator', 'N/A')
        
        # Extract first few pages content for analysis
        sample_text = ""
        pages_to_sample = min(5, len(reader.pages))
        
        for i in range(pages_to_sample):
            try:
                page_text = reader.pages[i].extract_text()
                sample_text += f"\n--- Page {i+1} ---\n{page_text[:1000]}\n"
            except Exception as e:
                sample_text += f"\n--- Page {i+1} (error extracting) ---\n"
        
        metadata['sample_content'] = sample_text
        
        # Try to extract some middle pages to understand structure
        if len(reader.pages) > 10:
            middle_page = len(reader.pages) // 2
            try:
                middle_text = reader.pages[middle_page].extract_text()
                metadata['middle_page_sample'] = f"\n--- Middle Page {middle_page+1} ---\n{middle_text[:1000]}\n"
            except:
                metadata['middle_page_sample'] = "Could not extract middle page"
        
        return metadata
        
    except Exception as e:
        return {
            'filename': os.path.basename(pdf_path),
            'error': str(e)
        }

def main():
    pdf_dir = r'c:\cod\licenta'
    
    # Find all PDFs
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    print(f"Found {len(pdf_files)} PDF files\n")
    print("=" * 80)
    
    all_analyses = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print(f"\nAnalyzing: {pdf_file}")
        print("-" * 80)
        
        analysis = analyze_pdf(pdf_path)
        all_analyses.append(analysis)
        
        # Print summary
        print(f"Pages: {analysis.get('num_pages', 'N/A')}")
        print(f"Size: {analysis.get('file_size_mb', 'N/A')} MB")
        print(f"Title: {analysis.get('title', 'N/A')}")
        print(f"Author: {analysis.get('author', 'N/A')}")
        
        if 'sample_content' in analysis:
            print(f"\nFirst few pages preview:")
            print(analysis['sample_content'][:2000])
        
        if 'error' in analysis:
            print(f"ERROR: {analysis['error']}")
    
    # Save full analysis to JSON
    output_file = os.path.join(pdf_dir, 'pdf_analysis.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_analyses, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"\nFull analysis saved to: pdf_analysis.json")

if __name__ == "__main__":
    main()
