"""
Smart OCR Pipeline with Image Enhancement and Confidence Tracking
Detects potential hallucinations by flagging low-confidence words
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import json
from datetime import datetime
from collections import defaultdict

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configure Poppler path for Windows (pdf2image)
POPPLER_PATH = r'C:\Users\TC\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin'


class SmartOCR:
    """
    Enhanced OCR with:
    1. Image preprocessing (OpenCV)
    2. Confidence scoring for each word
    3. Hallucination detection
    4. Manual review flagging
    """
    
    def __init__(self, confidence_threshold=60, languages='ron+eng'):
        """
        Args:
            confidence_threshold: Words below this confidence (0-100) are flagged
            languages: Tesseract language codes
        """
        self.confidence_threshold = confidence_threshold
        self.languages = languages
        self.review_items = []
        self.stats = {
            'total_pages': 0,
            'total_words': 0,
            'low_confidence_words': 0,
            'pages_needing_review': set()
        }
    
    def preprocess_image(self, image, enhance_level='medium'):
        """
        Apply image preprocessing to improve OCR quality
        
        Args:
            image: PIL Image or numpy array
            enhance_level: 'light', 'medium', 'heavy'
        
        Returns:
            Preprocessed image as numpy array
        """
        
        # Convert PIL to numpy if needed
        if isinstance(image, Image.Image):
            img = np.array(image)
        else:
            img = image.copy()
        
        # Convert to grayscale if color
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img
        
        if enhance_level == 'light':
            # Light: Just denoise and threshold
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        
        elif enhance_level == 'medium':
            # Medium: Denoise, contrast enhance, adaptive threshold
            
            # 1. Denoise
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            
            # 2. Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # 3. Adaptive thresholding for uneven lighting
            binary = cv2.adaptiveThreshold(
                enhanced, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 4. Slight morphological cleanup
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
        
        else:  # heavy
            # Heavy: All the above + deskewing + sharpening
            
            # 1. Resize up (super-resolution simulation)
            scale = 2
            enlarged = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
            # 2. Strong denoising
            denoised = cv2.fastNlMeansDenoising(enlarged, h=15)
            
            # 3. Sharpen
            kernel_sharp = np.array([[-1, -1, -1],
                                      [-1,  9, -1],
                                      [-1, -1, -1]])
            sharpened = cv2.filter2D(denoised, -1, kernel_sharp)
            
            # 4. CLAHE contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(sharpened)
            
            # 5. Adaptive threshold
            binary = cv2.adaptiveThreshold(
                enhanced, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 15, 4
            )
            
            # 6. Morphological cleanup
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            return cleaned
    
    def deskew_image(self, image):
        """Correct image rotation/skew"""
        
        # Convert to numpy if needed
        if isinstance(image, Image.Image):
            img = np.array(image)
        else:
            img = image.copy()
        
        # Convert to grayscale for angle detection
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img
        
        # Detect edges
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                 minLineLength=100, maxLineGap=10)
        
        if lines is None:
            return image
        
        # Calculate average angle
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if abs(angle) < 45:  # Only consider near-horizontal lines
                angles.append(angle)
        
        if not angles:
            return image
        
        median_angle = np.median(angles)
        
        # Only correct if significantly skewed
        if abs(median_angle) > 0.5:
            # Rotate image
            h, w = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h), 
                                      flags=cv2.INTER_CUBIC,
                                      borderMode=cv2.BORDER_REPLICATE)
            return rotated
        
        return image
    
    def ocr_with_confidence(self, image, page_num=1):
        """
        Perform OCR and get word-level confidence scores
        
        Returns:
            dict with:
                - text: full extracted text
                - words: list of {word, confidence, bbox}
                - low_confidence: list of suspicious words
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
                    'bbox': {
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'w': data['width'][i],
                        'h': data['height'][i]
                    },
                    'block': data['block_num'][i],
                    'line': data['line_num'][i]
                }
                
                words.append(word_info)
                full_text_parts.append(word)
                self.stats['total_words'] += 1
                
                # Flag low confidence words
                if conf < self.confidence_threshold and len(word) > 2:
                    low_confidence.append(word_info)
                    self.stats['low_confidence_words'] += 1
                    self.stats['pages_needing_review'].add(page_num)
        
        return {
            'text': ' '.join(full_text_parts),
            'words': words,
            'low_confidence': low_confidence,
            'avg_confidence': np.mean([w['confidence'] for w in words]) if words else 0
        }
    
    def process_pdf(self, pdf_path, output_dir, start_page=1, max_pages=None, 
                    enhance_level='medium', deskew=True):
        """
        Process a PDF with enhanced OCR
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Where to save results
            start_page: First page to process (1-indexed)
            max_pages: Maximum pages to process (None = all)
            enhance_level: 'light', 'medium', 'heavy'
            deskew: Whether to correct image rotation
        
        Returns:
            Results dictionary with text, confidence scores, and review items
        """
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        print(f"\n{'='*80}")
        print(f"SMART OCR PROCESSOR")
        print(f"{'='*80}")
        print(f"PDF: {Path(pdf_path).name}")
        print(f"Enhancement: {enhance_level}")
        print(f"Confidence threshold: {self.confidence_threshold}%")
        print(f"Languages: {self.languages}")
        
        # Convert PDF to images
        print(f"\n📄 Converting PDF to images...")
        
        try:
            images = convert_from_path(
                pdf_path,
                dpi=300,  # Higher DPI for better quality
                first_page=start_page,
                last_page=start_page + max_pages - 1 if max_pages else None,
                poppler_path=POPPLER_PATH
            )
        except Exception as e:
            print(f"❌ Error converting PDF: {e}")
            print("\nTrying without poppler_path...")
            images = convert_from_path(
                pdf_path,
                dpi=300,
                first_page=start_page,
                last_page=start_page + max_pages - 1 if max_pages else None
            )
        
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
            
            # 1. Deskew if enabled
            if deskew:
                img = self.deskew_image(img)
            
            # 2. Preprocess image
            processed = self.preprocess_image(img, enhance_level)
            
            # 3. OCR with confidence
            ocr_result = self.ocr_with_confidence(processed, page_num)
            
            # 4. Store results
            page_result = {
                'page': page_num,
                'text': ocr_result['text'],
                'word_count': len(ocr_result['words']),
                'avg_confidence': round(ocr_result['avg_confidence'], 1),
                'low_confidence_count': len(ocr_result['low_confidence'])
            }
            
            results['pages'].append(page_result)
            all_text.append(ocr_result['text'])
            
            # 5. Track items needing review
            if ocr_result['low_confidence']:
                review_item = {
                    'page': page_num,
                    'suspicious_words': [
                        {
                            'word': w['word'],
                            'confidence': w['confidence'],
                            'context': self._get_context(ocr_result['words'], w)
                        }
                        for w in ocr_result['low_confidence'][:10]  # Top 10 per page
                    ]
                }
                results['review_needed'].append(review_item)
            
            # Show status
            status = "✓" if ocr_result['avg_confidence'] > 70 else "⚠"
            flag = f" ⚠ {len(ocr_result['low_confidence'])} suspicious" if ocr_result['low_confidence'] else ""
            print(f"{status} {len(ocr_result['words'])} words, {ocr_result['avg_confidence']:.0f}% avg conf{flag}")
            
            # Save preprocessed image for debugging (first page only)
            if idx == 0:
                debug_path = output_dir / f'debug_page_{page_num}.png'
                cv2.imwrite(str(debug_path), processed)
                print(f"   💾 Debug image: {debug_path.name}")
        
        # Summary
        results['summary'] = {
            'total_pages': self.stats['total_pages'],
            'total_words': self.stats['total_words'],
            'low_confidence_words': self.stats['low_confidence_words'],
            'pages_needing_review': len(self.stats['pages_needing_review']),
            'hallucination_risk': round(
                (self.stats['low_confidence_words'] / max(1, self.stats['total_words'])) * 100, 2
            )
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
        print(f"🎯 Hallucination risk: {results['summary']['hallucination_risk']:.1f}%")
        print(f"\n📁 Output files:")
        print(f"   - {text_file}")
        print(f"   - {json_file}")
        print(f"   - {review_file}")
        
        return results
    
    def _get_context(self, words, target_word, window=3):
        """Get surrounding words for context"""
        
        target_idx = None
        for i, w in enumerate(words):
            if w['word'] == target_word['word'] and w['bbox'] == target_word['bbox']:
                target_idx = i
                break
        
        if target_idx is None:
            return ""
        
        start = max(0, target_idx - window)
        end = min(len(words), target_idx + window + 1)
        
        context_words = [w['word'] for w in words[start:end]]
        
        # Mark the target word
        relative_idx = target_idx - start
        if 0 <= relative_idx < len(context_words):
            context_words[relative_idx] = f"**{context_words[relative_idx]}**"
        
        return ' '.join(context_words)
    
    def _save_review_report(self, results, filepath):
        """Save a markdown report of items needing review"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# OCR Review Report\n\n")
            f.write(f"**Generated:** {results['processed_at']}\n\n")
            f.write(f"**PDF:** {results['pdf']}\n\n")
            
            f.write("## Summary\n\n")
            f.write(f"- Total pages: {results['summary']['total_pages']}\n")
            f.write(f"- Total words: {results['summary']['total_words']:,}\n")
            f.write(f"- Low confidence words: {results['summary']['low_confidence_words']:,}\n")
            f.write(f"- **Hallucination risk: {results['summary']['hallucination_risk']:.1f}%**\n\n")
            
            if not results['review_needed']:
                f.write("## ✅ No items need manual review!\n\n")
                f.write("All words were extracted with high confidence.\n")
            else:
                f.write("## ⚠ Pages Needing Review\n\n")
                f.write("The following words have low OCR confidence and may be incorrect.\n")
                f.write("Check the original PDF to verify.\n\n")
                
                for item in results['review_needed']:
                    f.write(f"### Page {item['page']}\n\n")
                    f.write("| Word | Confidence | Context |\n")
                    f.write("|------|------------|----------|\n")
                    
                    for word in item['suspicious_words']:
                        f.write(f"| `{word['word']}` | {word['confidence']}% | {word['context']} |\n")
                    
                    f.write("\n")


def main():
    """Test the smart OCR on first few pages"""
    
    pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
    output_dir = r'c:\cod\licenta\smart_ocr_results'
    
    print("\n" + "="*80)
    print("SMART OCR TEST - First 5 Pages")
    print("="*80)
    print("\nThis will:")
    print("1. Enhance image quality with OpenCV")
    print("2. Extract text with Tesseract")
    print("3. Track confidence for each word")
    print("4. Flag potential hallucinations for review\n")
    
    ocr = SmartOCR(
        confidence_threshold=60,  # Flag words below 60% confidence
        languages='ron+eng'       # Romanian + English
    )
    
    results = ocr.process_pdf(
        pdf_path,
        output_dir,
        start_page=10,      # Start at page 10 (likely has field data)
        max_pages=5,        # Process just 5 pages for testing
        enhance_level='medium',  # 'light', 'medium', or 'heavy'
        deskew=True
    )
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Review the generated files in:", output_dir)
    print("2. Check REVIEW_NEEDED.md for suspicious words")
    print("3. If quality is good, run full extraction with:")
    print("   python smart_ocr.py --full")


if __name__ == "__main__":
    import sys
    
    if '--full' in sys.argv:
        # Full extraction
        pdf_path = r'c:\cod\licenta\Paraschiv 1979 - Ro oil _ gas fields STE_Seria_A_vol_13.pdf'
        output_dir = r'c:\cod\licenta\smart_ocr_results'
        
        ocr = SmartOCR(confidence_threshold=60, languages='ron+eng')
        ocr.process_pdf(
            pdf_path, output_dir,
            start_page=1, max_pages=None,
            enhance_level='medium', deskew=True
        )
    else:
        main()
