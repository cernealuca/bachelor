"""
OCR Field Catalog - Direct PDF Upload to OCR.space
No Poppler needed - sends PDF directly to API
"""

import requests
import time
import json
from pathlib import Path

class DirectPDFOCR:
    """OCR PDF directly without image conversion"""
    
    def __init__(self, api_key='K87899142388957'):
        self.api_key = api_key
        self.api_url = 'https://api.ocr.space/parse/image'
        
    def ocr_pdf_direct(self, pdf_path, page_start=1, page_end=None):
        """
        OCR PDF pages directly
        API supports PDFs up to 5 pages at once on free tier
        """
        
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            print(f"Error: {pdf_file} not found")
            return None
        
        print(f"\n📄 Processing: {pdf_file.name}")
        print(f"   Pages: {page_start} to {page_end if page_end else 'end'}")
        
        try:
            with open(pdf_file, 'rb') as f:
                # Send PDF directly
                response = requests.post(
                    self.api_url,
                    files={'file': (pdf_file.name, f, 'application/pdf')},
                    data={
                        'apikey': self.api_key,
                        'language': 'eng',
                        'isOverlayRequired': False,
                        'detectOrientation': True,
                        'scale': True,
                        'OCREngine': 2,  # Engine 2 better for tables
                        'isTable': True   # Detect tables
                    },
                    timeout=120
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('IsErroredOnProcessing'):
                    error_msgs = result.get('ErrorMessage', ['Unknown error'])
                    print(f"   ✗ Error: {error_msgs}")
                    return None
                
                # Extract all pages
                pages_text = []
                if result.get('ParsedResults'):
                    for idx, page_result in enumerate(result['ParsedResults']):
                        text = page_result.get('ParsedText', '')
                        pages_text.append({
                            'page': page_start + idx,
                            'text': text,
                            'char_count': len(text)
                        })
                        print(f"   ✓ Page {page_start + idx}: {len(text)} characters")
                
                return pages_text
            else:
                print(f"   ✗ HTTP {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"   ✗ Exception: {e}")
            return None


def quick_test_direct():
    """Test direct PDF OCR on first pages"""
    
    pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
    
    print("\n" + "="*80)
    print("QUICK TEST: Direct PDF OCR (No Poppler Needed!)")
    print("="*80)
    print("\nTesting OCR.space with direct PDF upload...")
    print("This will process the first few pages to check quality\n")
    
    ocr = DirectPDFOCR()
    
    # OCR.space free tier processes max 1 page per request for PDFs
    # So we'll do it page by page, but send the whole PDF
    # The API will just process the first page
    
    results = ocr.ocr_pdf_direct(pdf_path, page_start=1)
    
    if results:
        print(f"\n✅ SUCCESS! Extracted {len(results)} page(s)")
        
        for page_data in results:
            print(f"\n{'─'*80}")
            print(f"Page {page_data['page']} ({page_data['char_count']} characters):")
            print(f"{'─'*80}")
            print(page_data['text'][:800])  # Show first 800 chars
            print("...")
        
        # Save result
        output_file = Path(r'c:\cod\licenta\ocr_test') / 'test_result.json'
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved to: {output_file}")
        
        print(f"\n{'='*80}")
        print("ANALYSIS:")
        print("="*80)
        print("1. Check if field names are visible in the text above")
        print("2. Look for Romanian place names, rock types, depths")
        print("3. If quality is good, we can proceed with batch processing")
        
        return True
    else:
        print("\n❌ OCR failed. Trying alternative approach...")
        return False


def batch_process_with_simple_ocr():
    """
    Alternative: Use simpler method that works without Poppler
    Convert to base64 and send directly
    """
    
    print("\n💡 ALT ERNATIVE: Let's try a different free OCR service")
    print("\nOptions:")
    print("1. Use Tesseract (free, install locally)")
    print("2. Use online converter first (smallpdf.com) then OCR")
    print("3. Process pages manually - extract most critical field data")
    print("\nFor now, let's see what we got from the basic extraction...")


def main():
    """Main execution"""
    
    success = quick_test_direct()
    
    if not success:
        print("\n🔄 Don't worry! We have alternatives:")
        print("1. Install Tesseract locally (100% free)")
        print("2. Use the data we already have (559 pages is already impressive!)")
        print("3. Manually digitize just the field index/table of contents")
        batch_process_with_simple_ocr()


if __name__ == "__main__":
    main()
