"""
Smart OCR Pipeline - Pillow Version (Python 3.14 Compatible)
Uses PIL for image preprocessing, Tesseract for OCR with confidence tracking
"""

from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
from pdf2image import convert_from_path
import json
from datetime import datetime

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configure Poppler path for Windows (pdf2image)
POPPLER_PATH = r'C:\Users\TC\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin'


class SmartOCR:
    """
    Enhanced OCR with:
    1. Image preprocessing (Pillow)
    2. Confidence scoring for each word
    3. Hallucination detection
    4. Manual review flagging
    """
    
    def __init__(self, confidence_threshold=60, languages='ron+eng'):
        self.confidence_threshold = confidence_threshold
        self.languages = languages
        self.stats = {
            'total_pages': 0,
            'total_words': 0,
            'low_confidence_words': 0,
            'pages_needing_review': set()
        }
    
    def preprocess_image(self, image, enhance_level='medium'):
        """
        Apply image preprocessing using Pillow
        
        Args:
            image: PIL Image
            enhance_level: 'light', 'medium', 'heavy'
        """
        
        # Convert to grayscale
        img = image.convert('L')
        
        if enhance_level == 'light':
            # Light: Just enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            return img
        
        elif enhance_level == 'medium':
            # Medium: Sharpen + contrast + auto-level
            
            # 1. Auto-level (normalize histogram)
            img = ImageOps.autocontrast(img, cutoff=1)
            
            # 2. Sharpen
            img = img.filter(ImageFilter.SHARPEN)
            
            # 3. Enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.8)
            
            # 4. Denoise slightly
            img = img.filter(ImageFilter.MedianFilter(size=3))
            
            return img
        
        else:  # heavy
            # Heavy: Resize up, sharpen, enhance, threshold
            
            # 1. Resize up 2x
            w, h = img.size
            img = img.resize((w * 2, h * 2), Image.LANCZOS)
            
            # 2. Strong sharpen
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
            
            # 3. Auto-level
            img = ImageOps.autocontrast(img, cutoff=2)
            
            # 4. High contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.5)
            
            # 5. Binarize (convert to pure black/white)
            threshold = 140
            img = img.point(lambda x: 255 if x > threshold else 0, 'L')
            
            return img
    
    def ocr_with_confidence(self, image, page_num=1):
        """
        Perform OCR and get word-level confidence scores
        """
        
        # Get detailed OCR data
        data = pytesseract.image_to_data(
            image, 
            lang=self.languages,
            output_type=pytesseract.Output.DICT,
            config='--psm 1'  # Auto page segmentation with OSD
        )
        
        words = []
        low_confidence = []
        full_text_parts = []
        
        n_boxes = len(data['text'])
        
        for i in range(n_boxes):
            word = data['text'][i].strip()
            conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
            
            if word:  # Skip empty entries
                word_info = {
                    'word': word,
                    'confidence': conf,
                    'page': page_num,
                    'line': data['line_num'][i]
                }
                
                words.append(word_info)
                full_text_parts.append(word)
                self.stats['total_words'] += 1
                
                # Flag low confidence words (only words with 3+ characters)
                if conf < self.confidence_threshold and len(word) > 2:
                    low_confidence.append(word_info)
                    self.stats['low_confidence_words'] += 1
                    self.stats['pages_needing_review'].add(page_num)
        
        avg_conf = sum(w['confidence'] for w in words) / len(words) if words else 0
        
        return {
            'text': ' '.join(full_text_parts),
            'words': words,
            'low_confidence': low_confidence,
            'avg_confidence': avg_conf
        }
    
    def _get_context(self, words, target_word, window=3):
        """Get surrounding words for context"""
        
        target_idx = None
        for i, w in enumerate(words):
            if w['word'] == target_word['word'] and w.get('line') == target_word.get('line'):
                target_idx = i
                break
        
        if target_idx is None:
            return target_word['word']
        
        start = max(0, target_idx - window)
        end = min(len(words), target_idx + window + 1)
        
        context_words = [w['word'] for w in words[start:end]]
        
        # Mark the target word
        relative_idx = target_idx - start
        if 0 <= relative_idx < len(context_words):
            context_words[relative_idx] = f"**{context_words[relative_idx]}**"
        
        return ' '.join(context_words)
    
    def process_pdf(self, pdf_path, output_dir, start_page=1, max_pages=None, 
                    enhance_level='medium'):
        """
        Process a PDF with enhanced OCR
        """
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        print(f"\n{'='*80}")
        print(f"SMART OCR PROCESSOR (Pillow Version)")
        print(f"{'='*80}")
        print(f"PDF: {Path(pdf_path).name}")
        print(f"Enhancement: {enhance_level}")
        print(f"Confidence threshold: {self.confidence_threshold}%")
        print(f"Languages: {self.languages}")
        
        # Convert PDF to images
        print(f"\n📄 Converting PDF to images (300 DPI)...")
        
        try:
            images = convert_from_path(
                pdf_path,
                dpi=300,
                first_page=start_page,
                last_page=start_page + max_pages - 1 if max_pages else None,
                poppler_path=POPPLER_PATH
            )
        except Exception as e:
            print(f"⚠ Trying without explicit poppler path...")
            try:
                images = convert_from_path(
                    pdf_path,
                    dpi=300,
                    first_page=start_page,
                    last_page=start_page + max_pages - 1 if max_pages else None
                )
            except Exception as e2:
                print(f"❌ Error: {e2}")
                return None
        
        total_pages = len(images)
        print(f"✓ Found {total_pages} pages to process")
        
        results = {
            'pdf': str(pdf_path),
            'processed_at': datetime.now().isoformat(),
            'settings': {
                'enhance_level': enhance_level,
                'confidence_threshold': self.confidence_threshold,
                'languages': self.languages,
                'dpi': 300
            },
            'pages': [],
            'review_needed': [],
            'summary': {}
        }
        
        all_text = []
        
        for idx, img in enumerate(images):
            page_num = start_page + idx
            self.stats['total_pages'] += 1
            
            print(f"\n[{idx+1}/{total_pages}] Page {page_num}...", end=' ')
            
            # 1. Preprocess image
            processed = self.preprocess_image(img, enhance_level)
            
            # 2. OCR with confidence
            ocr_result = self.ocr_with_confidence(processed, page_num)
            
            # 3. Store results
            page_result = {
                'page': page_num,
                'text': ocr_result['text'],
                'word_count': len(ocr_result['words']),
                'avg_confidence': round(ocr_result['avg_confidence'], 1),
                'low_confidence_count': len(ocr_result['low_confidence'])
            }
            
            results['pages'].append(page_result)
            all_text.append(ocr_result['text'])
            
            # 4. Track items needing review
            if ocr_result['low_confidence']:
                review_item = {
                    'page': page_num,
                    'suspicious_words': [
                        {
                            'word': w['word'],
                            'confidence': w['confidence'],
                            'context': self._get_context(ocr_result['words'], w)
                        }
                        for w in ocr_result['low_confidence'][:15]  # Top 15 per page
                    ]
                }
                results['review_needed'].append(review_item)
            
            # Show status
            status = "✓" if ocr_result['avg_confidence'] > 70 else "⚠"
            flag = f" ⚠ {len(ocr_result['low_confidence'])} suspicious" if ocr_result['low_confidence'] else ""
            print(f"{status} {len(ocr_result['words'])} words, {ocr_result['avg_confidence']:.0f}% avg conf{flag}")
            
            # Save preprocessed image for first page (debug)
            if idx == 0:
                debug_path = output_dir / f'debug_page_{page_num}.png'
                processed.save(debug_path)
                print(f"   💾 Debug image: {debug_path.name}")
        
        # Calculate summary
        hallucination_risk = (self.stats['low_confidence_words'] / max(1, self.stats['total_words'])) * 100
        
        results['summary'] = {
            'total_pages': self.stats['total_pages'],
            'total_words': self.stats['total_words'],
            'low_confidence_words': self.stats['low_confidence_words'],
            'pages_needing_review': len(self.stats['pages_needing_review']),
            'hallucination_risk': round(hallucination_risk, 2)
        }
        
        # Save full text
        text_file = output_dir / 'extracted_text.txt'
        with open(text_file, 'w', encoding='utf-8') as f:
            for i, text in enumerate(all_text):
                f.write(f"\n{'='*60}\n")
                f.write(f"PAGE {start_page + i}\n")
                f.write(f"{'='*60}\n\n")
                f.write(text)
                f.write("\n")
        
        # Save JSON results
        json_file = output_dir / 'ocr_results.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save review report
        review_file = output_dir / 'REVIEW_NEEDED.md'
        self._save_review_report(results, review_file)
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"✓ Pages processed: {self.stats['total_pages']}")
        print(f"✓ Words extracted: {self.stats['total_words']:,}")
        print(f"⚠ Low confidence words: {self.stats['low_confidence_words']:,}")
        print(f"📋 Pages needing review: {len(self.stats['pages_needing_review'])}")
        print(f"🎯 Hallucination risk: {hallucination_risk:.1f}%")
        print(f"\n📁 Output files:")
        print(f"   - {text_file}")
        print(f"   - {json_file}")
        print(f"   - {review_file}")
        
        return results
    
    def _save_review_report(self, results, filepath):
        """Save a markdown report of items needing review"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 🔍 OCR Review Report\n\n")
            f.write(f"**Generated:** {results['processed_at']}\n\n")
            f.write(f"**PDF:** `{Path(results['pdf']).name}`\n\n")
            
            f.write("## 📊 Summary\n\n")
            f.write(f"| Metric | Value |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Total pages | {results['summary']['total_pages']} |\n")
            f.write(f"| Total words | {results['summary']['total_words']:,} |\n")
            f.write(f"| Low confidence words | {results['summary']['low_confidence_words']:,} |\n")
            f.write(f"| Pages needing review | {results['summary']['pages_needing_review']} |\n")
            f.write(f"| **Hallucination risk** | **{results['summary']['hallucination_risk']:.1f}%** |\n\n")
            
            if results['summary']['hallucination_risk'] < 5:
                f.write("> ✅ **LOW RISK**: OCR quality is excellent!\n\n")
            elif results['summary']['hallucination_risk'] < 15:
                f.write("> ⚠️ **MEDIUM RISK**: Some words may need correction.\n\n")
            else:
                f.write("> 🔴 **HIGH RISK**: Many words need manual verification.\n\n")
            
            if not results['review_needed']:
                f.write("## ✅ No items need manual review!\n\n")
                f.write("All words were extracted with high confidence.\n")
            else:
                f.write("## ⚠️ Words Needing Review\n\n")
                f.write("The following words have low OCR confidence and may be incorrect.\n")
                f.write("Check the original PDF to verify. Words are shown **in bold** within context.\n\n")
                
                for item in results['review_needed']:
                    f.write(f"### 📄 Page {item['page']}\n\n")
                    f.write("| Word | Confidence | Context |\n")
                    f.write("|------|------------|----------|\n")
                    
                    for word in item['suspicious_words']:
                        escaped_word = word['word'].replace('|', '\\|')
                        escaped_context = word['context'].replace('|', '\\|')
                        f.write(f"| `{escaped_word}` | {word['confidence']}% | {escaped_context} |\n")
                    
                    f.write("\n")
            
            f.write("---\n\n")
            f.write("## How to Use This Report\n\n")
            f.write("1. **Open the original PDF** alongside this report\n")
            f.write("2. **Go to each page** listed in the review section\n")
            f.write("3. **Find the suspicious word** using the context provided\n")
            f.write("4. **Correct** any misread words in `extracted_text.txt`\n")
            f.write("5. Words with confidence < 60% are most likely to need correction\n")


def main():
    """Test the smart OCR on first few pages"""
    
    pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
    output_dir = r'c:\cod\licenta\smart_ocr_results_pil'
    
    print("\n" + "="*80)
    print("SMART OCR TEST - First 5 Pages")
    print("="*80)
    print("\nThis will:")
    print("1. Enhance image quality with PIL")
    print("2. Extract text with Tesseract (Romanian + English)")
    print("3. Track confidence for each word")
    print("4. Create a REVIEW_NEEDED.md report for suspicious words\n")
    
    ocr = SmartOCR(
        confidence_threshold=60,
        languages='ron+eng'
    )
    
    results = ocr.process_pdf(
        pdf_path,
        output_dir,
        start_page=10,
        max_pages=5,
        enhance_level='medium'
    )
    
    if results:
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print(f"\n1. Check the review report: {output_dir}\\REVIEW_NEEDED.md")
        print(f"2. Look at the debug image to verify preprocessing quality")
        print(f"3. If satisfied, run full extraction with:")
        print(f"   python smart_ocr_pil.py --full\n")


if __name__ == "__main__":
    import sys
    
    if '--full' in sys.argv:
        pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
        output_dir = r'c:\cod\licenta\smart_ocr_results_pil'
        
        print("\n🚀 FULL EXTRACTION MODE")
        print("This will process ALL pages in the PDF...\n")
        
        ocr = SmartOCR(confidence_threshold=60, languages='ron+eng')
        ocr.process_pdf(
            pdf_path, output_dir,
            start_page=1, max_pages=None,
            enhance_level='medium'
        )
    else:
        main()
