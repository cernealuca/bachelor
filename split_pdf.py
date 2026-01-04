"""
PDF Splitter for Batch OCR Processing
Splits large PDF into smaller chunks for free OCR API
"""

from pypdf import PdfReader, PdfWriter
from pathlib import Path
import os

def split_pdf_into_chunks(pdf_path, chunk_size=10, output_dir='pdf_chunks'):
    """
    Split PDF into smaller chunks
    
    Args:
        pdf_path: Path to large PDF
        chunk_size: Pages per chunk (10-20 pages keeps under 1MB usually)
        output_dir: Where to save chunks
    """
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    
    print(f"\n{'='*80}")
    print(f"SPLITTING PDF: {Path(pdf_path).name}")
    print(f"{'='*80}")
    print(f"Total pages: {total_pages}")
    print(f"Chunk size: {chunk_size} pages")
    print(f"Output: {output_dir}")
    
    chunk_files = []
    chunk_num = 1
    
    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size, total_pages)
        
        # Create new PDF for this chunk
        writer = PdfWriter()
        
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        # Save chunk
        chunk_filename = output_dir / f'chunk_{chunk_num:03d}_pages_{start_page+1}-{end_page}.pdf'
        with open(chunk_filename, 'wb') as f:
            writer.write(f)
        
        file_size_mb = os.path.getsize(chunk_filename) / (1024 * 1024)
        
        print(f"  ✓ Chunk {chunk_num}: Pages {start_page+1}-{end_page} ({file_size_mb:.2f} MB)")
        
        chunk_files.append({
            'chunk_num': chunk_num,
            'file': str(chunk_filename),
            'pages': f"{start_page+1}-{end_page}",
            'size_mb': file_size_mb
        })
        
        chunk_num += 1
    
    print(f"\n{'='*80}")
    print(f"✅ Created {len(chunk_files)} chunks")
    print(f"{'='*80}")
    
    return chunk_files


def estimate_api_calls(num_chunks):
    """Estimate time needed for free API (500/day limit, 10/minute rate limit)"""
    
    minutes_needed = num_chunks * 6  # 6 seconds per request
    hours_needed = minutes_needed / 60
    
    if num_chunks <= 500:
        print(f"\n⏱️  Estimated time: {hours_needed:.1f} hours (at 10 requests/minute)")
        print(f"   Can complete today (under 500/day limit)")
    else:
        days_needed = (num_chunks // 500) + 1
        print(f"\n⏱️  Estimated time: {days_needed} days")
        print(f"   (Free API limit: 500 requests/day)")


def main():
    """Main execution"""
    
    pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
    output_dir = r'c:\cod\licenta\pdf_chunks'
    
    # Split into 10-page chunks
    chunks = split_pdf_into_chunks(pdf_path, chunk_size=10, output_dir=output_dir)
    
    # Estimate API processing time
    estimate_api_calls(len(chunks))
    
    print(f"\n📝 Next steps:")
    print(f"1. Chunks are ready in: {output_dir}")
    print(f"2. Use ocr_chunks.py to process them with free OCR API")
    print(f"3. Or use tesseract_batch.py if Tesseract is installed")


if __name__ == "__main__":
    main()
