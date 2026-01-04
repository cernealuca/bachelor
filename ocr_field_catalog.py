"""
OCR.space API - Free OCR for 1979 Field Catalog
Processes the image-based PDF to extract field data
API: 500 requests/day free, no credit card needed
"""

import requests
import time
import json
from pathlib import Path
from pypdf import PdfReader
import pdf2image

class OCRSpaceProcessor:
    """Process PDF using OCR.space free API"""
    
    def __init__(self, api_key='K87899142388957'):
        """
        Initialize with OCR.space API key
        Default key is a public demo key (limited usage)
        Get your own free key at: https://ocr.space/ocrapi
        """
        self.api_key = api_key
        self.api_url = 'https://api.ocr.space/parse/image'
        self.session = requests.Session()
        
    def ocr_page_from_pdf(self, pdf_path, page_number):
        """
        Extract text from a specific page using OCR.space API
        """
        
        try:
            # Convert PDF page to image
            images = pdf2image.convert_from_path(
                pdf_path,
                first_page=page_number,
                last_page=page_number,
                dpi=200  # Good balance of quality and speed
            )
            
            if not images:
                return None
            
            # Save temporarily
            temp_image = Path('temp_page.png')
            images[0].save(temp_image, 'PNG')
            
            # Send to OCR.space API
            with open(temp_image, 'rb') as f:
                response = self.session.post(
                    self.api_url,
                    files={'file': f},
                    data={
                        'apikey': self.api_key,
                        'language': 'eng',  # Romanian uses Latin script
                        'isOverlayRequired': False,
                        'detectOrientation': True,
                        'scale': True,
                        'OCREngine': 2,  # Engine 2 is better for complex layouts
                    },
                    timeout=60
                )
            
            # Clean up temp file
            temp_image.unlink(missing_ok=True)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('IsErroredOnProcessing'):
                    error_msg = result.get('ErrorMessage', ['Unknown error'])
                    print(f"    ✗ OCR Error: {error_msg[0]}")
                    return None
                
                # Extract text
                if result.get('ParsedResults'):
                    text = result['ParsedResults'][0].get('ParsedText', '')
                    return text
            else:
                print(f"    ✗ API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"    ✗ Exception: {e}")
            return None
    
    def process_pdf_batch(self, pdf_path, start_page=1, max_pages=100, output_dir='ocr_results'):
        """
        Process a batch of pages from the PDF
        Free tier: 500 requests/day, so process in batches
        """
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Get total pages
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        
        print(f"\n{'='*80}")
        print(f"OCR PROCESSING: {Path(pdf_path).name}")
        print(f"{'='*80}")
        print(f"Total pages: {total_pages}")
        print(f"Processing: pages {start_page} to {min(start_page + max_pages - 1, total_pages)}")
        print(f"Using: OCR.space Free API")
        
        results = {
            'pdf': str(pdf_path),
            'pages_processed': [],
            'pages_failed': [],
            'total_characters': 0
        }
        
        end_page = min(start_page + max_pages, total_pages + 1)
        
        for page_num in range(start_page, end_page):
            print(f"\nPage {page_num}/{total_pages}...", end=' ')
            
            # OCR the page
            text = self.ocr_page_from_pdf(pdf_path, page_num)
            
            if text:
                print(f"✓ {len(text)} characters")
                
                results['pages_processed'].append({
                    'page': page_num,
                    'text': text,
                    'char_count': len(text)
                })
                
                results['total_characters'] += len(text)
                
                # Show preview of first page
                if page_num == start_page:
                    print(f"\n  Preview: {text[:200]}...")
            else:
                print("✗ Failed")
                results['pages_failed'].append(page_num)
            
            # Rate limiting - be nice to free API
            # Recommended: max 10 requests per minute
            if page_num < end_page - 1:
                time.sleep(6)  # 6 seconds = 10 requests/minute
        
        # Save results
        output_file = output_dir / f'ocr_pages_{start_page}_to_{end_page-1}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"BATCH COMPLETE")
        print(f"{'='*80}")
        print(f"✓ Processed: {len(results['pages_processed'])} pages")
        print(f"✗ Failed: {len(results['pages_failed'])} pages")
        print(f"📄 Total text: {results['total_characters']:,} characters")
        print(f"💾 Saved to: {output_file}")
        
        return results


def quick_test():
    """Test OCR on just a few pages first"""
    
    pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
    
    processor = OCRSpaceProcessor()
    
    print("\n🧪 QUICK TEST: Processing first 5 pages")
    print("This will help us verify OCR quality before processing all 394 pages\n")
    
    results = processor.process_pdf_batch(
        pdf_path,
        start_page=10,  # Start at page 10 (likely has field data, not just TOC)
        max_pages=5,
        output_dir=r'c:\cod\licenta\ocr_test'
    )
    
    if results['pages_processed']:
        print("\n✅ OCR is working! Quality check:")
        
        sample_page = results['pages_processed'][0]
        print(f"\nSample from page {sample_page['page']}:")
        print(f"{sample_page['text'][:500]}")
        
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("1. Review the sample above - does it look accurate?")
        print("2. If good, run full extraction (will take ~4-5 hours for 394 pages)")
        print("3. Or process in batches: 100 pages today, 100 tomorrow, etc.")
        print("\nReady to proceed with full extraction? (Y/N)")
    else:
        print("\n❌ OCR test failed. Check API key or try different pages.")


def full_extraction():
    """
    Process all 394 pages
    This will take several hours due to rate limiting (10 req/min)
    """
    
    pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
    
    processor = OCRSpaceProcessor()
    
    print("\n⚡ FULL EXTRACTION MODE")
    print("="*80)
    print("This will process all 394 pages.")
    print("Estimated time: ~4 hours (10 pages/min with rate limiting)")
    print("You can stop anytime (Ctrl+C) and resume later.")
    print("="*80)
    
    # Process in batches of 100
    batches = [
        (1, 100),
        (101, 200),
        (201, 300),
        (301, 394)
    ]
    
    for start, end in batches:
        batch_size = end - start + 1
        print(f"\n\n📦 BATCH: Pages {start}-{end} ({batch_size} pages)")
        
        results = processor.process_pdf_batch(
            pdf_path,
            start_page=start,
            max_pages=batch_size,
            output_dir=r'c:\cod\licenta\ocr_results'
        )
        
        print(f"\n✅ Batch {start}-{end} complete!")
        print(f"Taking 30-second break before next batch...\n")
        time.sleep(30)
    
    print("\n" + "="*80)
    print("🎉 FULL EXTRACTION COMPLETE!")
    print("="*80)
    print("Next: Combine all batches and update knowledge graph")


def main():
    """Main execution"""
    
    import sys
    
    if '--test' in sys.argv:
        quick_test()
    elif '--full' in sys.argv:
        full_extraction()
    else:
        print("\nUsage:")
        print("  python ocr_field_catalog.py --test   # Test on 5 pages first")
        print("  python ocr_field_catalog.py --full   # Process all 394 pages")
        print("\nRecommended: Start with --test to verify quality")


if __name__ == "__main__":
    main()
