"""
Romanian OCR Post-Processor
Automatically corrects common OCR errors in Romanian text
Logs all corrections for manual review
"""

import re
from difflib import SequenceMatcher
from collections import defaultdict


class RomanianCorrector:
    """
    Post-OCR correction for Romanian geographical and geological text
    Uses pattern matching and known corrections to fix common errors
    """
    
    def __init__(self):
        # Known Romanian place names with their common OCR misreadings
        self.place_corrections = {
            'dimbovita': 'Dambovita',
            'dambovita': 'Dambovita',
            'caransebes': 'Caransebes',
            'qaransebes': 'Caransebes',
            'qoaransebes': 'Caransebes',
            'oaransebes': 'Caransebes',
            'ploiesti': 'Ploiesti',
            'bucuresti': 'Bucuresti',
            'timisoara': 'Timisoara',
            'brasov': 'Brasov',
            'constanta': 'Constanta',
            'targoviste': 'Targoviste',
            'tirgoviste': 'Targoviste',
            'buzau': 'Buzau',
            'bacau': 'Bacau',
            'galati': 'Galati',
            'birlad': 'Barlad',
            'moinesti': 'Moinesti',
            'tescani': 'Tescani',
            'lucacesti': 'Lucacesti',
            'pacureti': 'Pacureti',
            'tazlaul': 'Tazlaul',
            'sarmasel': 'Sarmasel',
            'hateg': 'Hateg',
            'petrosani': 'Petrosani',
            'ciucurilor': 'Ciucurilor',
            'beius': 'Beius',
            'mures': 'Mures',
            'oltenia': 'Oltenia',
            'muntenia': 'Muntenia',
            'moldova': 'Moldova',
            'moldavia': 'Moldova',
            'transylvania': 'Transilvania',
            'transilvania': 'Transilvania',
            'dobrogea': 'Dobrogea',
            'mosoare': 'Mosoare',
            'pacura': 'Pacura',
            'gaiceana': 'Gaiceana',
            'glavanesti': 'Glavanesti',
            'murgeni': 'Murgeni',
        }
        
        # Romanian person names (geologists, scientists)
        self.person_corrections = {
            'grigorasg': 'Grigoras',
            'grigorass': 'Grigoras',
            'grigorag': 'Grigoras',
            'cobilcescu': 'Cobilcescu',
            'mrazec': 'Mrazec',
            'mrazeec': 'Mrazec',
            'paraschiv': 'Paraschiv',
            'murgoei': 'Murgoci',
            'murgoci': 'Murgoci',
            'vancea': 'Vancea',
            'ciupagea': 'Ciupagea',
            'oiupagea': 'Ciupagea',
            'atanasiu': 'Atanasiu',
            'teisseyre': 'Teisseyre',
            'botez': 'Botez',
            'sandulescu': 'Sandulescu',
            'dumitrescu': 'Dumitrescu',
            'stefanescu': 'Stefanescu',
            'bogdanof': 'Bogdanov',
            'preda': 'Preda',
            'cantemir': 'Cantemir',
        }
        
        # Geological terms commonly misread
        self.geological_corrections = {
            'erystalline': 'crystalline',
            'crystailine': 'crystalline',
            'schits': 'schists',
            'shists': 'schists',
            'sehists': 'schists',
            'flyseh': 'flysch',
            'geosynclinex': 'geosynclines',
            'anticlins': 'anticlines',
            'banatites': 'banatites',
            'granodiorites': 'granodiorites',
            'diabases': 'diabases',
            'palaeozoic': 'Paleozoic',
            'paleozic': 'Paleozoic',
            'mesozic': 'Mesozoic',
            'mesozoie': 'Mesozoic',
            'cretaceoous': 'Cretaceous',
            'cretaeeous': 'Cretaceous',
            'jurassie': 'Jurassic',
            'triassie': 'Triassic',
            'hydroearbons': 'hydrocarbons',
            'hydrocarbonx': 'hydrocarbons',
            'petroleun': 'petroleum',
            'petrolum': 'petroleum',
            'petrolem': 'petroleum',
            'voleanoes': 'volcanoes',
            'voleanic': 'volcanic',
        }
        
        # Incomplete/truncated words (OCR cut-off errors)
        self.incomplete_corrections = {
            'oi': 'oil',
            'oI': 'oil',
            'oIl': 'oil',
            'oii': 'oil',
            'oll': 'oil',
            'ol': 'oil',
            'gAs': 'gas',
            'GAs': 'GAS',
            'gaS': 'gas',
            'petroleu': 'petroleum',
            'petrole': 'petroleum',
            'geolog': 'geology',
            'geologica': 'geological',
            'formatio': 'formation',
            'depositio': 'deposition',
            'accumulatio': 'accumulation',
            'exploitatio': 'exploitation',
            'extractio': 'extraction',
            'explorati': 'exploration',
            'carpath': 'Carpathian',
            'carpathia': 'Carpathian',
        }
        
        # Common multi-word phrase corrections
        self.phrase_corrections = {
            'oi and gas': 'oil and gas',
            'oil and gAs': 'oil and gas',
            'oIl and gas': 'oil and gas',
            'OI AND GAS': 'OIL AND GAS',
            'OI AND GAs': 'OIL AND GAS',
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
        }
        
        # Build combined dictionary
        self.all_corrections = {}
        for d in [self.place_corrections, self.person_corrections, 
                  self.geological_corrections, self.incomplete_corrections]:
            for k, v in d.items():
                self.all_corrections[k.lower()] = v
        
        # Track corrections made
        self.correction_log = []
        self.stats = defaultdict(int)
    
    def similarity(self, a, b):
        """Calculate string similarity ratio"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def find_best_correction(self, word, threshold=0.7):
        """Find the best correction for a word based on similarity"""
        word_clean = word.lower().strip('.,;:!?"\'()[]')
        
        # Direct match
        if word_clean in self.all_corrections:
            return self.all_corrections[word_clean], 1.0
        
        # Fuzzy match
        best_match = None
        best_score = 0
        
        for known, correction in self.all_corrections.items():
            score = self.similarity(word_clean, known)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = correction
        
        return best_match, best_score
    
    def correct_word(self, word, context="", page=0):
        """Attempt to correct a single word"""
        original = word
        prefix = ""
        suffix = ""
        
        # Extract leading punctuation
        punct_chars = '.,;:!?"\'()[]'
        while word and word[0] in punct_chars:
            prefix += word[0]
            word = word[1:]
        
        # Extract trailing punctuation
        while word and len(word) > 0 and word[-1] in punct_chars:
            suffix = word[-1] + suffix
            word = word[:-1]
        
        if not word:
            return original, False, None
        
        correction, confidence = self.find_best_correction(word)
        
        if correction and correction.lower() != word.lower():
            corrected = prefix + correction + suffix
            
            log_entry = {
                'page': page,
                'original': original,
                'corrected': corrected,
                'confidence': round(confidence * 100, 1),
                'context': context,
                'type': self._get_correction_type(word)
            }
            
            self.correction_log.append(log_entry)
            self.stats['corrections'] += 1
            self.stats[log_entry['type']] += 1
            
            return corrected, True, log_entry
        
        return original, False, None
    
    def _get_correction_type(self, word):
        """Determine the type of correction"""
        word_lower = word.lower()
        if word_lower in self.place_corrections:
            return 'place_name'
        elif word_lower in self.person_corrections:
            return 'person_name'
        elif word_lower in self.geological_corrections:
            return 'geological_term'
        elif word_lower in self.incomplete_corrections:
            return 'incomplete_word'
        return 'other'
    
    def apply_phrase_corrections(self, text):
        """Apply multi-word phrase corrections"""
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
                    'type': 'phrase'
                })
        return text
    
    def correct_text(self, text, page=0):
        """Correct an entire text block"""
        # First apply phrase corrections
        text = self.apply_phrase_corrections(text)
        
        # Split into words
        words = text.split()
        corrected_words = []
        
        for i, word in enumerate(words):
            # Get context
            start = max(0, i - 3)
            end = min(len(words), i + 4)
            context = ' '.join(words[start:end])
            
            corrected, was_changed, _ = self.correct_word(word, context, page)
            corrected_words.append(corrected)
        
        return ' '.join(corrected_words)
    
    def get_correction_report(self):
        """Generate a detailed markdown report of all corrections"""
        
        lines = []
        lines.append("# OCR Correction Report\n")
        lines.append("## Summary\n")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Total corrections | {self.stats['corrections']} |")
        lines.append(f"| Place names | {self.stats.get('place_name', 0)} |")
        lines.append(f"| Person names | {self.stats.get('person_name', 0)} |")
        lines.append(f"| Geological terms | {self.stats.get('geological_term', 0)} |")
        lines.append(f"| Incomplete words | {self.stats.get('incomplete_word', 0)} |")
        lines.append(f"| Phrase fixes | {self.stats.get('phrase_corrections', 0)} |")
        lines.append("")
        
        if not self.correction_log:
            lines.append("## No corrections needed!")
            return '\n'.join(lines)
        
        # Group by page
        by_page = defaultdict(list)
        for entry in self.correction_log:
            by_page[entry['page']].append(entry)
        
        lines.append("## Corrections by Page\n")
        
        for page in sorted(by_page.keys()):
            lines.append(f"### Page {page}\n")
            lines.append("| Original | Corrected | Type | Confidence |")
            lines.append("|----------|-----------|------|------------|")
            
            for entry in by_page[page]:
                orig = entry['original'].replace('|', '\\|')
                corr = entry['corrected'].replace('|', '\\|')
                lines.append(f"| `{orig}` | `{corr}` | {entry['type']} | {entry['confidence']}% |")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def reset(self):
        """Reset correction tracking"""
        self.correction_log = []
        self.stats = defaultdict(int)


# Quick test
if __name__ == "__main__":
    corrector = RomanianCorrector()
    
    test_words = [
        "Dimbovita",
        "QOaransebes",
        "Grigorasg",
        "erystalline",
        "hydroearbons",
        "Ploiesti",
        "Mrazeec",
        "OI",
        "GAs",
    ]
    
    print("=" * 60)
    print("ROMANIAN OCR CORRECTOR - TEST")
    print("=" * 60)
    
    for word in test_words:
        corrected, changed, log = corrector.correct_word(word)
        if changed:
            print(f"  {word} -> {corrected}")
        else:
            print(f"  {word} (no change)")
    
    print("\n" + corrector.get_correction_report())
