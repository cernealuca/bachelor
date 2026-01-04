"""
Smart OCR with Post-Processing Corrections
Combines OCR extraction with Romanian text correction
Outputs detailed change logs
"""

from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
from pdf2image import convert_from_path
import json
from datetime import datetime
from romanian_corrector import RomanianCorrector

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
POPPLER_PATH = r'C:\Users\TC\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin'


class SmartOCRWithCorrection:
    """
    Enhanced OCR with:
    1. Image preprocessing
    2. Tesseract OCR with confidence tracking
    3. Post-OCR Romanian text correction
    4. Detailed change logging
    """
    
    def __init__(self, confidence_threshold=60, languages='ron+eng'):
        self.confidence_threshold = confidence_threshold
        self.languages = languages
        self.corrector = RomanianCorrector()
        self.stats = {
            'total_pages': 0,
            'total_words': 0,
            'low_confidence_words': 0,
            'corrections_made': 0,
        }
    
    def preprocess_image(self, image):
        """Apply image preprocessing"""
        img = image.convert('L')
        img = ImageOps.autocontrast(img, cutoff=1)
        img = img.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.8)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        return img
    
    def ocr_with_confidence(self, image, page_num=1):
        """Perform OCR and get word-level confidence"""
        data = pytesseract.image_to_data(
            image, 
            lang=self.languages,
            output_type=pytesseract.Output.DICT,
            config='--psm 1'
        )
        
        words = []
        low_confidence = []
        text_parts = []
        
        for i in range(len(data['text'])):
            word = data['text'][i].strip()
            conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
            
            if word:
                word_info = {
                    'word': word,
                    'confidence': conf,
                    'page': page_num,
                    'line': data['line_num'][i]
                }
                words.append(word_info)
                text_parts.append(word)
                self.stats['total_words'] += 1
                
                if conf < self.confidence_threshold and len(word) > 2:
                    low_confidence.append(word_info)
                    self.stats['low_confidence_words'] += 1
        
        avg_conf = sum(w['confidence'] for w in words) / len(words) if words else 0
        
        return {
            'text': ' '.join(text_parts),
            'words': words,
            'low_confidence': low_confidence,
            'avg_confidence': avg_conf
        }
    
    def process_pdf(self, pdf_path, output_dir, start_page=1, max_pages=None):
        """Process PDF with OCR and correction"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        print(f"\n{'='*70}")
        print(f"SMART OCR WITH CORRECTION")
        print(f"{'='*70}")
        print(f"PDF: {Path(pdf_path).name}")
        print(f"Languages: {self.languages}")
        
        # Convert PDF to images
        print(f"\nConverting PDF to images (300 DPI)...")
        
        try:
            images = convert_from_path(
                pdf_path, dpi=300,
                first_page=start_page,
                last_page=start_page + max_pages - 1 if max_pages else None,
                poppler_path=POPPLER_PATH
            )
        except:
            images = convert_from_path(
                pdf_path, dpi=300,
                first_page=start_page,
                last_page=start_page + max_pages - 1 if max_pages else None
            )
        
        total_pages = len(images)
        print(f"Found {total_pages} pages to process\n")
        
        all_text_raw = []
        all_text_corrected = []
        page_results = []
        
        for idx, img in enumerate(images):
            page_num = start_page + idx
            self.stats['total_pages'] += 1
            
            print(f"[{idx+1}/{total_pages}] Page {page_num}...", end=' ')
            
            # 1. Preprocess
            processed = self.preprocess_image(img)
            
            # 2. OCR
            ocr_result = self.ocr_with_confidence(processed, page_num)
            raw_text = ocr_result['text']
            all_text_raw.append(raw_text)
            
            # 3. Correct
            corrected_text = self.corrector.correct_text(raw_text, page_num)
            all_text_corrected.append(corrected_text)
            
            # Count corrections on this page
            page_corrections = len([c for c in self.corrector.correction_log 
                                   if c['page'] == page_num])
            
            page_results.append({
                'page': page_num,
                'word_count': len(ocr_result['words']),
                'avg_confidence': round(ocr_result['avg_confidence'], 1),
                'low_confidence_count': len(ocr_result['low_confidence']),
                'corrections_made': page_corrections
            })
            
            # Status
            status = "OK" if ocr_result['avg_confidence'] > 70 else "!!"
            corr_note = f" [{page_corrections} fixed]" if page_corrections > 0 else ""
            print(f"{status} {len(ocr_result['words'])} words, "
                  f"{ocr_result['avg_confidence']:.0f}% conf{corr_note}")
        
        self.stats['corrections_made'] = len(self.corrector.correction_log)
        
        # Save outputs
        self._save_outputs(output_dir, all_text_raw, all_text_corrected, 
                          page_results, start_page)
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"COMPLETE")
        print(f"{'='*70}")
        print(f"Pages: {self.stats['total_pages']}")
        print(f"Words: {self.stats['total_words']:,}")
        print(f"Low confidence: {self.stats['low_confidence_words']:,}")
        print(f"Corrections made: {self.stats['corrections_made']}")
        print(f"\nOutput: {output_dir}")
        
        return page_results
    
    def _save_outputs(self, output_dir, raw_texts, corrected_texts, 
                      page_results, start_page):
        """Save all output files"""
        
        # 1. Raw OCR text
        raw_file = output_dir / 'extracted_text_RAW.txt'
        with open(raw_file, 'w', encoding='utf-8') as f:
            for i, text in enumerate(raw_texts):
                f.write(f"\n{'='*60}\n")
                f.write(f"PAGE {start_page + i} (RAW OCR)\n")
                f.write(f"{'='*60}\n\n")
                f.write(text + "\n")
        
        # 2. Corrected text
        corrected_file = output_dir / 'extracted_text_CORRECTED.txt'
        with open(corrected_file, 'w', encoding='utf-8') as f:
            for i, text in enumerate(corrected_texts):
                f.write(f"\n{'='*60}\n")
                f.write(f"PAGE {start_page + i} (CORRECTED)\n")
                f.write(f"{'='*60}\n\n")
                f.write(text + "\n")
        
        # 3. Correction report
        report_file = output_dir / 'CORRECTIONS_MADE.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# OCR Corrections Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write("## Summary\n\n")
            f.write(f"- Pages processed: {self.stats['total_pages']}\n")
            f.write(f"- Total words: {self.stats['total_words']:,}\n")
            f.write(f"- Low confidence words: {self.stats['low_confidence_words']:,}\n")
            f.write(f"- **Corrections made: {self.stats['corrections_made']}**\n\n")
            f.write(self.corrector.get_correction_report())
        
        # 4. JSON data
        json_file = output_dir / 'ocr_data.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': self.stats,
                'pages': page_results,
                'corrections': self.corrector.correction_log
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved:")
        print(f"  - {raw_file.name} (original OCR)")
        print(f"  - {corrected_file.name} (with fixes)")
        print(f"  - {report_file.name} (change log)")
        print(f"  - {json_file.name} (data)")


def main():
    """Test on first 5 pages"""
    
    pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
    output_dir = r'c:\cod\licenta\smart_ocr_corrected'
    
    print("\n" + "="*70)
    print("SMART OCR WITH AUTO-CORRECTION - TEST")
    print("="*70)
    print("\nThis will:")
    print("1. Extract text with Tesseract OCR")
    print("2. Auto-correct Romanian names and terms")
    print("3. Log all changes for your review\n")
    
    ocr = SmartOCRWithCorrection(confidence_threshold=60, languages='ron+eng')
    ocr.process_pdf(pdf_path, output_dir, start_page=10, max_pages=5)
    
    print("\nDone! Check CORRECTIONS_MADE.md to see what was changed.")


if __name__ == "__main__":
    import sys
    
    if '--full' in sys.argv:
        pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
        output_dir = r'c:\cod\licenta\smart_ocr_corrected'
        
        print("\nFULL EXTRACTION MODE\n")
        ocr = SmartOCRWithCorrection(confidence_threshold=60, languages='ron+eng')
        ocr.process_pdf(pdf_path, output_dir, start_page=1, max_pages=None)
    else:
        main()
