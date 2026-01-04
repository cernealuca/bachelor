"""
Tesseract Batch OCR Processor
Processes PDF pages using locally installed Tesseract
REQUIRES: Tesseract installed on system
"""

import subprocess
from pathlib import Path
import json
from pypdf import PdfReader
import time

class TesseractBatchOCR:
    """Process PDFs with Tesseract OCR"""
    
    def __init__(self, tesseract_path='tesseract'):
        """
        Initialize with Tesseract path
        If installed via installer, usually in PATH as 'tesseract'
        Otherwise specify full path: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        """
        self.tesseract_cmd = tesseract_path
        
    def check_tesseract(self):
        """Check if Tesseract is installed"""
        try:
            result = subprocess.run(
                [self.tesseract_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_info = result.stdout.split('\n')[0]
                print(f"✓ Found: {version_info}")
                return True
            else:
                print(f"✗ Tesseract not found in PATH")
                return False
                
        except FileNotFoundError:
            print(f"✗ Tesseract not installed or not in PATH")
            print(f"\nInstall from: https://github.com/UB-Mannheim/tesseract/wiki")
            return False
        except Exception as e:
            print(f"✗ Error checking Tesseract: {e}")
            return False
    
    def ocr_pdf_chunk(self, pdf_chunk_path, output_dir='tesseract_results'):
        """
        OCR a PDF chunk using Tesseract
        Tesseract can process PDF files directly!
        """
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        pdf_name = Path(pdf_chunk_path).stem
        txt_output = output_dir / f'{pdf_name}.txt'
        
        try:
            # Tesseract command: tesseract input.pdf output -l ron pdf
            # -l ron = Romanian language
            # Will create output.txt
            
            print(f"  Processing: {Path(pdf_chunk_path).name}...", end=' ')
            
            result = subprocess.run(
                [
                    self.tesseract_cmd,
                    str(pdf_chunk_path),
                    str(txt_output.with_suffix('')),  # Tesseract adds .txt
                    '-l', 'ron',  # Romanian language
                    '--psm', '1',  # Automatic page segmentation with OSD
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per chunk
            )
            
            if result.returncode == 0 and txt_output.exists():
                # Read extracted text
                with open(txt_output, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                print(f"✓ {len(text)} characters")
                return text
            else:
                print(f"✗ Failed")
                print(f"   Error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"✗ Timeout")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None
    
    def process_all_chunks(self, chunks_dir='pdf_chunks', output_dir='tesseract_results'):
        """Process all PDF chunks"""
        
        chunks_dir = Path(chunks_dir)
        
        if not chunks_dir.exists():
            print(f"✗ Chunks directory not found: {chunks_dir}")
            print(f"   Run split_pdf.py first!")
            return None
        
        chunk_files = sorted(chunks_dir.glob('chunk_*.pdf'))
        
        print(f"\n{'='*80}")
        print(f"TESSERACT BATCH OCR")
        print(f"{'='*80}")
        print(f"Chunks to process: {len(chunk_files)}")
        print(f"Output directory: {output_dir}")
        
        results = {
            'chunks_processed': [],
            'total_characters': 0,
            'failures': []
        }
        
        start_time = time.time()
        
        for idx, chunk_file in enumerate(chunk_files, 1):
            print(f"\n[{idx}/{len(chunk_files)}]", end=' ')
            
            text = self.ocr_pdf_chunk(chunk_file, output_dir)
            
            if text:
                results['chunks_processed'].append({
                    'chunk': str(chunk_file.name),
                    'char_count': len(text),
                    'text_preview': text[:200]
                })
                results['total_characters'] += len(text)
            else:
                results['failures'].append(str(chunk_file.name))
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"✓ Processed: {len(results['chunks_processed'])} chunks")
        print(f"✗ Failed: {len(results['failures'])} chunks")
        print(f"📄 Total text: {results['total_characters']:,} characters")
        print(f"⏱️  Time taken: {elapsed_time/60:.1f} minutes")
        
        # Save results
        results_file = Path(output_dir) / 'batch_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {results_file}")
        
        return results


def main():
    """Main execution"""
    
    print("\n" + "="*80)
    print("TESSERACT OCR - BATCH PROCESSOR")
    print("="*80)
    
    ocr = TesseractBatchOCR()
    
    # Check if Tesseract is installed
    print("\nChecking Tesseract installation...")
    if not ocr.check_tesseract():
        print("\n❌ Tesseract not found!")
        print("\n📥 Installation instructions:")
        print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Run installer: tesseract-ocr-w64-setup-5.3.3.xxxxx.exe")
        print("3. During installation, check 'Romanian' language pack")
        print("4. Run this script again")
        return
    
    # Check for chunks
    chunks_dir = Path(r'c:\cod\licenta\pdf_chunks')
    
    if not chunks_dir.exists() or not list(chunks_dir.glob('chunk_*.pdf')):
        print(f"\n📦 No PDF chunks found!")
        print(f"\n➡️  Run split_pdf.py first to create chunks:")
        print(f"   python split_pdf.py")
        return
    
    # Process all chunks
    print(f"\n🚀 Starting batch OCR processing...")
    print(f"   This will take approximately 20-30 minutes for ~40 chunks")
    print(f"   You can leave it running!\n")
    
    input("Press ENTER to start...")
    
    results = ocr.process_all_chunks(
        chunks_dir=r'c:\cod\licenta\pdf_chunks',
        output_dir=r'c:\cod\licenta\tesseract_results'
    )
    
    if results:
        print(f"\n✅ SUCCESS! Field catalog extracted!")
        print(f"\n📝 Next step: Combine results and update knowledge graph")
        print(f"   Run: python update_knowledge_with_fields.py")


if __name__ == "__main__":
    main()
