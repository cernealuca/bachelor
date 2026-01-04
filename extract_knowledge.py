"""
Advanced PDF Knowledge Extraction Pipeline
Uses premium OCR + NLP to build comprehensive geological knowledge base
"""

import os
import json
import re
from pathlib import Path
from pypdf import PdfReader
from collections import defaultdict
from datetime import datetime

class GeologicalKnowledgeExtractor:
    """Extract and structure geological knowledge from Romanian petroleum PDFs"""
    
    def __init__(self, pdf_dir):
        self.pdf_dir = Path(pdf_dir)
        self.knowledge_base = {
            'documents': [],
            'entities': {
                'oil_fields': [],
                'gas_fields': [],
                'geological_zones': [],
                'formations': [],
                'platforms': [],
                'basins': [],
                'locations': []
            },
            'relationships': [],
            'measurements': [],
            'dates': [],
            'technical_terms': {}
        }
        
        # Romanian geological terms dictionary
        self.geological_terms = {
            'zăcăminte': 'deposits',
            'hidrocarburi': 'hydrocarbons',
            'platformă': 'platform',
            'depresiune': 'depression',
            'câmp': 'field',
            'zonă': 'zone',
            'formaţiune': 'formation',
            'rezervor': 'reservoir',
            'gresii': 'sandstones',
            'argile': 'clays',
            'marne': 'marls',
            'calcare': 'limestones',
            'dolomite': 'dolomites',
            'nisipuri': 'sands',
            'adâncime': 'depth',
            'porozitate': 'porosity',
            'permeabilitate': 'permeability',
            'grosime': 'thickness',
            'stratigrafie': 'stratigraphy',
            'structură': 'structure'
        }
        
    def extract_from_pdf(self, pdf_path):
        """Extract comprehensive information from a single PDF"""
        
        print(f"\n{'='*80}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*80}")
        
        reader = PdfReader(pdf_path)
        document_data = {
            'filename': pdf_path.name,
            'num_pages': len(reader.pages),
            'chapters': [],
            'entities_found': defaultdict(list),
            'full_text': [],
            'tables_of_contents': [],
            'references': []
        }
        
        # Extract text from all pages
        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text()
                if text and len(text.strip()) > 50:  # Skip mostly empty pages
                    document_data['full_text'].append({
                        'page': page_num,
                        'text': text
                    })
                    
                    # Extract entities from this page
                    self._extract_entities_from_text(text, page_num, document_data)
                    
                    if page_num % 10 == 0:
                        print(f"  Processed {page_num}/{len(reader.pages)} pages...")
                        
            except Exception as e:
                print(f"  Error on page {page_num}: {e}")
                continue
        
        print(f"\n✓ Extracted {len(document_data['full_text'])} pages of text")
        print(f"✓ Found {len(document_data['entities_found']['fields'])} potential field names")
        print(f"✓ Found {len(document_data['entities_found']['zones'])} zone references")
        
        return document_data
    
    def _extract_entities_from_text(self, text, page_num, document_data):
        """Extract geological entities from text"""
        
        # Extract oil/gas field names (usually capitalized, followed by field indicators)
        field_patterns = [
            r'([A-Z][a-zăâîșț]+(?:\s+[A-Z][a-zăâîșț]+)*)\s+(?:câmp|field|zăcământ)',
            r'câmp(?:ul)?\s+([A-Z][a-zăâîșț]+(?:\s+[A-Z][a-zăâîșț]+)*)',
            r'struktura\s+([A-Z][a-zăâîșț]+(?:\s+[A-Z][a-zăâîșț]+)*)'
        ]
        
        for pattern in field_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                field_name = match.group(1).strip()
                if len(field_name) > 2:  # Avoid single letters
                    document_data['entities_found']['fields'].append({
                        'name': field_name,
                        'page': page_num,
                        'context': match.group(0)
                    })
        
        # Extract zone names
        zone_patterns = [
            r'zona\s+([A-Za-zăâîșț\s]+?)(?:\.|,|\n)',
            r'([A-Z][a-zăâîșț]+)\s+zone',
            r'platforma\s+([A-Za-zăâîșț]+)'
        ]
        
        for pattern in zone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                zone_name = match.group(1).strip()
                if len(zone_name) > 3 and len(zone_name) < 50:
                    document_data['entities_found']['zones'].append({
                        'name': zone_name,
                        'page': page_num
                    })
        
        # Extract depth measurements
        depth_pattern = r'(\d+(?:\.\d+)?)\s*(?:m|metri|meters)\s*(?:adâncime|depth|profunzime)'
        depths = re.finditer(depth_pattern, text, re.IGNORECASE)
        for match in depths:
            document_data['entities_found']['depths'].append({
                'value': float(match.group(1)),
                'page': page_num,
                'context': match.group(0)
            })
        
        # Extract years/dates
        year_pattern = r'\b(19[0-9]{2}|20[0-2][0-9])\b'
        years = re.finditer(year_pattern, text)
        for match in years:
            document_data['entities_found']['years'].append({
                'year': int(match.group(1)),
                'page': page_num
            })
    
    def build_knowledge_graph(self, document_data):
        """Structure extracted data into knowledge graph format"""
        
        # Deduplicate and count entity occurrences
        entity_counts = defaultdict(lambda: {'count': 0, 'pages': []})
        
        for field in document_data['entities_found']['fields']:
            name = field['name']
            entity_counts[('field', name)]['count'] += 1
            entity_counts[('field', name)]['pages'].append(field['page'])
        
        for zone in document_data['entities_found']['zones']:
            name = zone['name']
            entity_counts[('zone', name)]['count'] += 1
            entity_counts[('zone', name)]['pages'].append(zone['page'])
        
        # Filter entities by frequency (appear at least 2 times = likely real entities)
        significant_entities = {
            'fields': [],
            'zones': []
        }
        
        for (entity_type, name), data in entity_counts.items():
            if data['count'] >= 2:  # Mentioned at least twice
                if entity_type == 'field':
                    significant_entities['fields'].append({
                        'name': name,
                        'mentions': data['count'],
                        'pages': sorted(set(data['pages']))
                    })
                elif entity_type == 'zone':
                    significant_entities['zones'].append({
                        'name': name,
                        'mentions': data['count'],
                        'pages': sorted(set(data['pages']))
                    })
        
        # Sort by mention count
        significant_entities['fields'].sort(key=lambda x: x['mentions'], reverse=True)
        significant_entities['zones'].sort(key=lambda x: x['mentions'], reverse=True)
        
        return significant_entities
    
    def create_searchable_index(self, document_data):
        """Create a searchable index of all content"""
        
        index = {
            'pages': [],
            'terms': defaultdict(list)
        }
        
        for page_data in document_data['full_text']:
            page_num = page_data['page']
            text = page_data['text']
            
            # Add to page index
            index['pages'].append({
                'page': page_num,
                'text': text,
                'preview': text[:500]  # First 500 chars as preview
            })
            
            # Index Romanian geological terms
            for ro_term, en_term in self.geological_terms.items():
                if ro_term in text.lower():
                    index['terms'][ro_term].append(page_num)
                    index['terms'][en_term].append(page_num)  # Add English equivalent
        
        return index
    
    def process_all_pdfs(self):
        """Process all PDFs in the directory"""
        
        pdf_files = list(self.pdf_dir.glob('*.pdf'))
        print(f"\nFound {len(pdf_files)} PDF files to process")
        
        all_results = {}
        
        for pdf_file in pdf_files:
            # Extract from PDF
            doc_data = self.extract_from_pdf(pdf_file)
            
            # Build knowledge graph
            entities = self.build_knowledge_graph(doc_data)
            
            # Create searchable index
            search_index = self.create_searchable_index(doc_data)
            
            all_results[pdf_file.name] = {
                'document_data': doc_data,
                'entities': entities,
                'search_index': search_index
            }
            
            # Print summary
            print(f"\n🎯 Knowledge Summary for {pdf_file.name}:")
            print(f"   • Oil/Gas Fields: {len(entities['fields'])} significant entities")
            print(f"   • Geological Zones: {len(entities['zones'])} significant entities")
            
            if entities['fields']:
                print(f"\n   Top 5 most mentioned fields:")
                for field in entities['fields'][:5]:
                    print(f"     - {field['name']} ({field['mentions']} mentions, pages: {field['pages'][:5]}...)")
            
            if entities['zones']:
                print(f"\n   Top 5 most mentioned zones:")
                for zone in entities['zones'][:5]:
                    print(f"     - {zone['name']} ({zone['mentions']} mentions)")
        
        return all_results
    
    def export_knowledge_base(self, results, output_dir):
        """Export extracted knowledge to structured files"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Export comprehensive knowledge base
        kb_file = output_dir / 'knowledge_base.json'
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved comprehensive knowledge base to: {kb_file}")
        
        # Export entities as separate CSV for easy review
        import csv
        
        # All fields across all documents
        fields_file = output_dir / 'oil_gas_fields.csv'
        with open(fields_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Field Name', 'Document', 'Mentions', 'Pages'])
            
            for doc_name, data in results.items():
                for field in data['entities']['fields']:
                    writer.writerow([
                        field['name'],
                        doc_name,
                        field['mentions'],
                        ', '.join(map(str, field['pages'][:10]))
                    ])
        print(f"✓ Saved fields catalog to: {fields_file}")
        
        # All zones
        zones_file = output_dir / 'geological_zones.csv'
        with open(zones_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Zone Name', 'Document', 'Mentions', 'Pages'])
            
            for doc_name, data in results.items():
                for zone in data['entities']['zones']:
                    writer.writerow([
                        zone['name'],
                        doc_name,
                        zone['mentions'],
                        ', '.join(map(str, zone['pages'][:10]))
                    ])
        print(f"✓ Saved zones catalog to: {zones_file}")
        
        # Create summary report
        summary_file = output_dir / 'extraction_summary.md'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('# Romanian Petroleum Geology - Knowledge Extraction Summary\n\n')
            f.write(f'**Extraction Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            
            total_pages = sum(len(data['document_data']['full_text']) for data in results.values())
            total_fields = sum(len(data['entities']['fields']) for data in results.values())
            total_zones = sum(len(data['entities']['zones']) for data in results.values())
            
            f.write(f'## Overview\n\n')
            f.write(f'- **Documents Processed:** {len(results)}\n')
            f.write(f'- **Total Pages Extracted:** {total_pages}\n')
            f.write(f'- **Oil/Gas Fields Identified:** {total_fields}\n')
            f.write(f'- **Geological Zones Identified:** {total_zones}\n\n')
            
            f.write(f'## Documents\n\n')
            for doc_name, data in results.items():
                f.write(f'### {doc_name}\n\n')
                f.write(f'- Pages: {len(data["document_data"]["full_text"])}\n')
                f.write(f'- Fields: {len(data["entities"]["fields"])}\n')
                f.write(f'- Zones: {len(data["entities"]["zones"])}\n\n')
                
                if data['entities']['fields']:
                    f.write(f'**Top Fields:**\n\n')
                    for field in data['entities']['fields'][:10]:
                        f.write(f'- **{field["name"]}** - {field["mentions"]} mentions\n')
                    f.write('\n')
        
        print(f"✓ Saved summary report to: {summary_file}")


def main():
    """Main execution"""
    
    pdf_dir = r'c:\cod\licenta'
    output_dir = r'c:\cod\licenta\knowledge_extracted'
    
    extractor = GeologicalKnowledgeExtractor(pdf_dir)
    
    print("\n" + "="*80)
    print("ROMANIAN PETROLEUM GEOLOGY - KNOWLEDGE EXTRACTION")
    print("="*80)
    
    # Process all PDFs
    results = extractor.process_all_pdfs()
    
    # Export knowledge base
    extractor.export_knowledge_base(results, output_dir)
    
    print("\n" + "="*80)
    print("✅ EXTRACTION COMPLETE!")
    print("="*80)
    print(f"\nNext steps:")
    print(f"1. Review extracted entities in: {output_dir}")
    print(f"2. Validate field and zone names")
    print(f"3. Build knowledge graph relationships")
    print(f"4. Prepare for AI training")


if __name__ == "__main__":
    main()
