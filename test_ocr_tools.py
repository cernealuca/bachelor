"""
Free OCR Comparison Tool for Romanian Geological PDFs
Tests Tesseract, EasyOCR, and PaddleOCR on the image-based PDF
"""

import os
import time
from pathlib import Path
from pypdf import PdfReader
import json

class OCRComparison:
    """Compare different free OCR solutions"""
    
    def __init__(self):
        self.results = {}
        self.test_pdf = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
        
    def test_tesseract(self, page_image):
        """Test Tesseract OCR with Romanian language"""
        try:
            import pytesseract
            from PIL import Image
            
            # Test with Romanian language pack
            text = pytesseract.image_to_string(page_image, lang='ron')
            return {
                'success': True,
                'text': text,
                'length': len(text),
                'tool': 'Tesseract 5.x'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': 'Tesseract 5.x'
            }
    
    def test_easyocr(self, page_image):
        """Test EasyOCR with Romanian"""
        try:
            import easyocr
            import numpy as np
            
            # Initialize reader for Romanian (once)
            if not hasattr(self, 'easyocr_reader'):
                print("    Initializing EasyOCR for Romanian...")
                self.easyocr_reader = easyocr.Reader(['ro'], gpu=False)
            
            # Convert PIL Image to numpy array
            img_array = np.array(page_image)
            
            # Perform OCR
            result = self.easyocr_reader.readtext(img_array)
            
            # Extract text
            text = ' '.join([detection[1] for detection in result])
            
            return {
                'success': True,
                'text': text,
                'length': len(text),
                'tool': 'EasyOCR',
                'detections': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': 'EasyOCR'
            }
    
    def test_paddleocr(self, page_image):
        """Test PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            
            # Initialize PaddleOCR (once)
            if not hasattr(self, 'paddle_ocr'):
                print("    Initializing PaddleOCR...")
                self.paddle_ocr = PaddleOCR(
                    lang='en',  # Use English model for Latin script
                    use_angle_cls=True,
                    use_gpu=False,
                    show_log=False
                )
            
            # Convert to numpy array
            img_array = np.array(page_image)
            
            # Perform OCR
            result = self.paddle_ocr.ocr(img_array, cls=True)
            
            # Extract text
            if result and result[0]:
                text = ' '.join([line[1][0] for line in result[0]])
            else:
                text = ''
            
            return {
                'success': True,
                'text': text,
                'length': len(text),
                'tool': 'PaddleOCR',
                'detections': len(result[0]) if result and result[0] else 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': 'PaddleOCR'
            }
    
    def extract_page_as_image(self, page_num):
        """Extract a PDF page as an image"""
        try:
            from pdf2image import convert_from_path
            
            # Convert specific page to image
            images = convert_from_path(
                self.test_pdf,
                first_page=page_num,
                last_page=page_num,
                dpi=300  # High DPI for better OCR
            )
            
            return images[0] if images else None
            
        except Exception as e:
            print(f"Error extracting page {page_num}: {e}")
            return None
    
    def run_comparison(self, test_pages=[10, 50, 100]):
        """Run comparison on multiple pages"""
        
        print("\n" + "="*80)
        print("FREE OCR COMPARISON FOR ROMANIAN GEOLOGICAL PDFs")
        print("="*80)
        
        print(f"\nTesting PDF: {Path(self.test_pdf).name}")
        print(f"Test pages: {test_pages}")
        
        for page_num in test_pages:
            print(f"\n{'─'*80}")
            print(f"Testing Page {page_num}")
            print(f"{'─'*80}")
            
            # Extract page as image
            print("  Extracting page as image (300 DPI)...")
            page_image = self.extract_page_as_image(page_num)
            
            if page_image is None:
                print(f"  ✗ Failed to extract page {page_num}")
                continue
            
            page_results = {'page': page_num, 'ocr_results': []}
            
            # Test each OCR tool
            print("\n  Testing Tesseract...")
            start = time.time()
            tesseract_result = self.test_tesseract(page_image)
            tesseract_result['time_seconds'] = round(time.time() - start, 2)
            page_results['ocr_results'].append(tesseract_result)
            
            if tesseract_result['success']:
                print(f"    ✓ Success: {tesseract_result['length']} characters in {tesseract_result['time_seconds']}s")
            else:
                print(f"    ✗ Failed: {tesseract_result['error']}")
            
            print("\n  Testing EasyOCR...")
            start = time.time()
            easyocr_result = self.test_easyocr(page_image)
            easyocr_result['time_seconds'] = round(time.time() - start, 2)
            page_results['ocr_results'].append(easyocr_result)
            
            if easyocr_result['success']:
                print(f"    ✓ Success: {easyocr_result['length']} characters, {easyocr_result.get('detections', 0)} detections in {easyocr_result['time_seconds']}s")
            else:
                print(f"    ✗ Failed: {easyocr_result['error']}")
            
            print("\n  Testing PaddleOCR...")
            start = time.time()
            paddle_result = self.test_paddleocr(page_image)
            paddle_result['time_seconds'] = round(time.time() - start, 2)
            page_results['ocr_results'].append(paddle_result)
            
            if paddle_result['success']:
                print(f"    ✓ Success: {paddle_result['length']} characters, {paddle_result.get('detections', 0)} detections in {paddle_result['time_seconds']}s")
            else:
                print(f"    ✗ Failed: {paddle_result['error']}")
            
            self.results[f'page_{page_num}'] = page_results
            
            # Show text preview from best result
            best_result = max(
                [r for r in page_results['ocr_results'] if r['success']],
                key=lambda x: x.get('length', 0),
                default=None
            )
            
            if best_result:
                print(f"\n  📄 Best result ({best_result['tool']}): Preview first 300 chars:")
                print(f"  {best_result['text'][:300]}...")
        
        # Save results
        output_file = r'c:\cod\licenta\ocr_comparison_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n{'='*80}")
        print(f"Results saved to: {output_file}")
        self.print_summary()
    
    def print_summary(self):
        """Print comparison summary"""
        
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        
        # Aggregate by tool
        tool_stats = {}
        
        for page_key, page_data in self.results.items():
            for result in page_data['ocr_results']:
                tool = result['tool']
                if tool not in tool_stats:
                    tool_stats[tool] = {
                        'successes': 0,
                        'failures': 0,
                        'total_chars': 0,
                        'total_time': 0,
                        'pages': 0
                    }
                
                if result['success']:
                    tool_stats[tool]['successes'] += 1
                    tool_stats[tool]['total_chars'] += result.get('length', 0)
                    tool_stats[tool]['total_time'] += result.get('time_seconds', 0)
                    tool_stats[tool]['pages'] += 1
                else:
                    tool_stats[tool]['failures'] += 1
        
        # Print stats
        for tool, stats in tool_stats.items():
            print(f"\n{tool}:")
            print(f"  Success rate: {stats['successes']}/{stats['successes']+stats['failures']}")
            if stats['pages'] > 0:
                print(f"  Avg characters: {stats['total_chars']//stats['pages']}")
                print(f"  Avg time: {stats['total_time']/stats['pages']:.2f}s")
        
        # Recommendation
        if tool_stats:
            best_tool = max(tool_stats.items(), key=lambda x: x[1]['total_chars'])
            print(f"\n🏆 RECOMMENDATION: {best_tool[0]}")
            print(f"   (Extracted most text: {best_tool[1]['total_chars']} total characters)")


def main():
    """Main execution"""
    
    comparator = OCRComparison()
    
    # Test on pages 10, 50, and 100 to get variety
    comparator.run_comparison(test_pages=[10, 50, 100])
    
    print("\n" + "="*80)
    print("Next step: Use the winning OCR tool to extract all 394 pages")
    print("="*80)


if __name__ == "__main__":
    main()
