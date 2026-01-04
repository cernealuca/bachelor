"""
Romanian OCR Post-Processor - CONSERVATIVE VERSION
Only corrects EXACT matches of known OCR errors
No fuzzy matching that could change legitimate words
"""

import re
from collections import defaultdict


class RomanianCorrector:
    """
    Conservative OCR correction - ONLY fixes exact known errors
    Will NOT change legitimate words like 'deposits', 'consists', etc.
    """
    
    def __init__(self):
        # ONLY exact OCR errors - these are words that are NEVER correct
        # Maps: wrong OCR reading -> correct word
        
        self.exact_corrections = {
            # === PLACE NAMES (exact OCR misreads) ===
            'qoaransebes': 'Caransebes',
            'qaransebes': 'Caransebes',
            'oaransebes': 'Caransebes',
            
            # === PERSON NAMES (exact OCR misreads) ===
            'grigorasg': 'Grigoras',
            'grigorass': 'Grigoras',
            'grigorag': 'Grigoras',
            'mrazeec': 'Mrazec',
            'oiupagea': 'Ciupagea',
            
            # === GEOLOGICAL TERMS (exact OCR misreads) ===
            'erystalline': 'crystalline',
            'crystailine': 'crystalline',
            'hydroearbons': 'hydrocarbons',
            'hydrocarbonx': 'hydrocarbons',
            'petroleun': 'petroleum',
            'petrolum': 'petroleum',
            'petrolem': 'petroleum',
            'voleanoes': 'volcanoes',
            'voleanic': 'volcanic',
            'schits': 'schists',  # Only this exact misspelling
            'shists': 'schists',
            'sehists': 'schists',
            'flyseh': 'flysch',
            'geosynclinex': 'geosynclines',
            'anticlins': 'anticlines',
            
            # === INCOMPLETE WORDS (clear OCR truncation) ===
            # Only very specific cases where it's clearly an error
        }
        
        # Phrase corrections - hyphenated word breaks from line endings
        self.phrase_corrections = {
            'for- mations': 'formations',
            'for- mation': 'formation',
            'forma- tions': 'formations',
            'forma- tion': 'formation',
            'geo- logical': 'geological',
            'geo- logy': 'geology',
            'hydro- carbons': 'hydrocarbons',
            'hydro-carbons': 'hydrocarbons',
            'anti- cline': 'anticline',
            'anti- clines': 'anticlines',
            'Pre- carpathian': 'Precarpathian',
            'pre- carpathian': 'Precarpathian',
            'colla- borate': 'collaborate',
            'men- tioning': 'mentioning',
            'Promon- tory': 'Promontory',
            'Car- pathians': 'Carpathians',
            'Car- pathian': 'Carpathian',
            'crystal- line': 'crystalline',
            'Transyl- vanian': 'Transylvanian',
            'Meso- zoic': 'Mesozoic',
            'Paleo- zoic': 'Paleozoic',
            'Creta- ceous': 'Cretaceous',
        }
        
        # Track corrections
        self.correction_log = []
        self.stats = defaultdict(int)
    
    def correct_word(self, word, context="", page=0):
        """
        Correct a single word - ONLY exact matches
        """
        original = word
        
        # Extract punctuation
        prefix = ""
        suffix = ""
        punct = '.,;:!?"\'()[]'
        
        while word and word[0] in punct:
            prefix += word[0]
            word = word[1:]
        
        while word and len(word) > 0 and word[-1] in punct:
            suffix = word[-1] + suffix
            word = word[:-1]
        
        if not word:
            return original, False, None
        
        # Check for EXACT match only (case-insensitive lookup)
        word_lower = word.lower()
        
        if word_lower in self.exact_corrections:
            correction = self.exact_corrections[word_lower]
            corrected = prefix + correction + suffix
            
            log_entry = {
                'page': page,
                'original': original,
                'corrected': corrected,
                'confidence': 100.0,
                'context': context,
                'type': 'exact_match'
            }
            
            self.correction_log.append(log_entry)
            self.stats['exact_corrections'] += 1
            
            return corrected, True, log_entry
        
        return original, False, None
    
    def apply_phrase_corrections(self, text):
        """Fix hyphenated line-break words"""
        original = text
        
        for wrong, correct in self.phrase_corrections.items():
            if wrong in text:
                text = text.replace(wrong, correct)
                self.stats['phrase_corrections'] += 1
                self.correction_log.append({
                    'page': 0,
                    'original': wrong,
                    'corrected': correct,
                    'confidence': 100.0,
                    'context': '',
                    'type': 'phrase_fix'
                })
        
        return text
    
    def correct_text(self, text, page=0):
        """Correct text - phrases first, then exact word matches"""
        
        # 1. Fix hyphenated breaks
        text = self.apply_phrase_corrections(text)
        
        # 2. Fix exact word matches only
        words = text.split()
        corrected_words = []
        
        for i, word in enumerate(words):
            start = max(0, i - 3)
            end = min(len(words), i + 4)
            context = ' '.join(words[start:end])
            
            corrected, _, _ = self.correct_word(word, context, page)
            corrected_words.append(corrected)
        
        return ' '.join(corrected_words)
    
    def get_correction_report(self):
        """Generate report"""
        lines = []
        lines.append("# OCR Corrections Report (Conservative Mode)\n")
        lines.append("Only EXACT matches of known OCR errors were corrected.\n")
        lines.append("## Summary\n")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        lines.append(f"| Exact word fixes | {self.stats.get('exact_corrections', 0)} |")
        lines.append(f"| Phrase/hyphen fixes | {self.stats.get('phrase_corrections', 0)} |")
        lines.append(f"| **Total** | {len(self.correction_log)} |")
        lines.append("")
        
        if not self.correction_log:
            lines.append("## No corrections needed!")
            return '\n'.join(lines)
        
        # Group by page
        by_page = defaultdict(list)
        for entry in self.correction_log:
            by_page[entry['page']].append(entry)
        
        lines.append("## All Corrections\n")
        
        for page in sorted(by_page.keys()):
            if page == 0:
                lines.append("### Phrase Fixes (line breaks)\n")
            else:
                lines.append(f"### Page {page}\n")
            
            lines.append("| OCR Error | Fixed To | Type |")
            lines.append("|-----------|----------|------|")
            
            for entry in by_page[page]:
                orig = entry['original'].replace('|', '\\|')
                corr = entry['corrected'].replace('|', '\\|')
                lines.append(f"| `{orig}` | `{corr}` | {entry['type']} |")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def reset(self):
        """Reset tracking"""
        self.correction_log = []
        self.stats = defaultdict(int)


# Test
if __name__ == "__main__":
    corrector = RomanianCorrector()
    
    # Test words - mix of real errors and legitimate words
    test_cases = [
        # These SHOULD be corrected (OCR errors)
        ("QOaransebes", True),
        ("Grigorasg", True),
        ("erystalline", True),
        ("hydroearbons", True),
        ("Mrazeec", True),
        
        # These should NOT be corrected (legitimate words)
        ("deposits", False),
        ("consists", False),
        ("formations", False),
        ("Carpathians", False),
        ("geologists", False),
        ("Transylvanian", False),
        ("Moldavian", False),
        ("natives", False),
        ("content", False),
        ("more", False),
        ("beings", False),
        ("old", False),
        ("as", False),
    ]
    
    print("=" * 60)
    print("CONSERVATIVE OCR CORRECTOR - TEST")
    print("=" * 60)
    
    all_correct = True
    for word, should_change in test_cases:
        corrected, was_changed, _ = corrector.correct_word(word)
        
        status = ""
        if was_changed == should_change:
            if was_changed:
                status = f"FIXED: {word} -> {corrected}"
            else:
                status = f"KEPT: {word} (correct)"
        else:
            status = f"ERROR: {word} was {'changed' if was_changed else 'kept'} but should {'change' if should_change else 'stay'}"
            all_correct = False
        
        print(f"  {status}")
    
    print()
    if all_correct:
        print("All tests passed!")
    else:
        print("SOME TESTS FAILED - check above")
