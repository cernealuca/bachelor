"""
GraphRAG Implementation for Romanian Petroleum Geology
Builds knowledge graph from extracted PDF text
Uses lightweight approach without heavy dependencies
"""

import json
import re
from collections import defaultdict
from pathlib import Path
import networkx as nx
from typing import List, Dict, Set, Tuple

class GeologicalGraphBuilder:
    """
    Build a knowledge graph from geological text
    Focuses on entities and relationships specific to petroleum geology
    """
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()  # Support multiple relationships between nodes
        self.entities = {
            'platforms': set(),
            'basins': set(),
            'zones': set(),
            'fields': set(),
            'formations': set(),
            'rocks': set(),
            'processes': set()
        }
        
        # Romanian-English terminology mapping
        self.terminology = {
            # Geological structures
            'platformă moesică': ('platform', 'Moesian Platform'),
            'platforma moldovenească': ('platform', 'Moldavian Platform'),
            'depresiunea precarpatică': ('basin', 'Pre-Carpathian Depression'),
            'depresiunea transilvaniei': ('basin', 'Transylvanian Basin'),
            'depresiunea getică': ('basin', 'Getic Depression'),
            
            # Rock types
            'gresii': ('rock', 'sandstones'),
            'marne': ('rock', 'marls'),
            'calcare': ('rock', 'limestones'),
            'nisipuri': ('rock', 'sands'),
            'argile': ('rock', 'shales'),
            'dolomite': ('rock', 'dolomites'),
            
            # Zones
            'zona estică': ('zone', 'Eastern Zone'),
            'zona centrală': ('zone', 'Central Zone'),
            'zona vestică': ('zone', 'Western Zone'),
            'zona flișului': ('zone', 'Flysch Zone'),
            
            # Geological ages
            'neogen': ('age', 'Neogene'),
            'paleogen': ('age', 'Paleogene'),
            'cretacic': ('age', 'Cretaceous'),
            'jurasic': ('age', 'Jurassic'),
            'triasic': ('age', 'Triassic'),
            
            # Hydrocarbon related
            'hidrocarburi': ('substance', 'hydrocarbons'),
            'petrol': ('substance', 'oil'),
            'gaz': ('substance', 'gas'),
            'rezervor': ('feature', 'reservoir'),
            'zăcământ': ('feature', 'deposit'),
        }
    
    def load_extracted_data(self, data_dir):
        """Load the previously extracted knowledge"""
        
        knowledge_file = Path(data_dir) / 'knowledge_base.json'
        
        if not knowledge_file.exists():
            print(f"ERROR: {knowledge_file} not found!")
            return None
        
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_entities_from_document(self, doc_name, document_data):
        """Extract named entities from document text"""
        
        print(f"\n  Processing: {doc_name}")
       
        # Process each page
        for page_item in document_data['document_data']['full_text']:
            text = page_item['text']
            page_num = page_item['page']
            
            # Extract entities using terminology dictionary
            for ro_term, (entity_type, en_term) in self.terminology.items():
                # Case-insensitive search
                pattern = re.compile(re.escape(ro_term), re.IGNORECASE)
                if pattern.search(text):
                    # Add to graph
                    node_id = f"{entity_type}:{en_term}"
                    
                    if not self.graph.has_node(node_id):
                        self.graph.add_node(
                            node_id,
                            name=en_term,
                            romanian_name=ro_term,
                            type=entity_type,
                            mentions=[]
                        )
                    
                    # Track mentions
                    self.graph.nodes[node_id]['mentions'].append({
                        'document': doc_name,
                        'page': page_num
                    })
                    
                    # Add to entity catalog
                    if entity_type == 'platform' or entity_type == 'basin':
                        self.entities['platforms'].add(en_term)
                    elif entity_type == 'zone':
                        self.entities['zones'].add(en_term)
                    elif entity_type == 'rock':
                        self.entities['rocks'].add(en_term)
            
            # Also extract from previously identified entities
            if 'entities' in document_data:
                for zone in document_data['entities'].get('zones', []):
                    zone_name = zone['name']
                    node_id = f"zone:{zone_name}"
                    
                    if not self.graph.has_node(node_id):
                        self.graph.add_node(
                            node_id,
                            name=zone_name,
                            type='zone',
                            mentions=zone.get('pages', [])
                        )
                    self.entities['zones'].add(zone_name)
        
        print(f"    ✓ Added nodes to graph")
    
    def extract_relationships(self, knowledge_base):
        """
        Extract relationships between entities based on co-occurrence and context
        """
        
        print("\n  Extracting relationships...")
        
        relationship_patterns = [
            (r'([\w\s]+)\s+din\s+([\w\s]+)', 'part_of'),  # "X of Y" (X part of Y)
            (r'([\w\s]+)\s+cuprinde\s+([\w\s]+)', 'contains'),  # "X contains Y"
            (r'([\w\s]+)\s+se\s+găsește\s+în\s+([\w\s]+)', 'located_in'),  # "X is found in Y"
        ]
        
        for doc_name, doc_data in knowledge_base.items():
            for page_item in doc_data['document_data']['full_text']:
                text = page_item['text']
                
                # Find entities mentioned together in same sentence
                sentences = text.split('.')
                
                for sentence in sentences:
                    entities_in_sentence = []
                    
                    # Find all entities in this sentence
                    for ro_term, (entity_type, en_term) in self.terminology.items():
                        if ro_term.lower() in sentence.lower():
                            entities_in_sentence.append((entity_type, en_term))
                    
                    # Create co-occurrence relationships
                    if len(entities_in_sentence) >= 2:
                        for i, (type1, entity1) in enumerate(entities_in_sentence):
                            for type2, entity2 in entities_in_sentence[i+1:]:
                                node1_id = f"{type1}:{entity1}"
                                node2_id = f"{type2}:{entity2}"
                                
                                if self.graph.has_node(node1_id) and self.graph.has_node(node2_id):
                                    # Add relationship (with weight for frequency)
                                    if self.graph.has_edge(node1_id, node2_id):
                                        # Increment weight
                                        for key in self.graph[node1_id][node2_id]:
                                            self.graph[node1_id][node2_id][key]['weight'] += 1
                                    else:
                                        self.graph.add_edge(
                                            node1_id,
                                            node2_id,
                                            relationship='co_mentioned',
                                            weight=1
                                        )
        
        print(f"    ✓ Added {self.graph.number_of_edges()} relationships")
    
    def build_graph(self, data_dir):
        """Main method to build the knowledge graph"""
        
        print("\n" + "="*80)
        print("BUILDING GEOLOGICAL KNOWLEDGE GRAPH")
        print("="*80)
        
        # Load extracted data
        print("\nLoading extracted knowledge...")
        knowledge_base = self.load_extracted_data(data_dir)
        
        if not knowledge_base:
            return False
        
        print(f"✓ Loaded {len(knowledge_base)} documents")
        
        # Extract entities
        print("\nExtracting entities...")
        for doc_name, doc_data in knowledge_base.items():
            self.extract_entities_from_document(doc_name, doc_data)
        
        print(f"\n  Total nodes in graph: {self.graph.number_of_nodes()}")
        
        # Extract relationships
        self.extract_relationships(knowledge_base)
        
        print(f"\n  Total edges in graph: {self.graph.number_of_edges()}")
        
        return True
    
    def save_graph(self, output_dir):
        """Save the knowledge graph in multiple formats"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Save as pickle file (for Python access)
        import pickle
        graph_file = output_dir / 'geological_graph.pkl'
        with open(graph_file, 'wb') as f:
            pickle.dump(self.graph, f)
        print(f"\n✓ Saved NetworkX graph: {graph_file}")
        
        # Save as GraphML (for visualization tools)
        graphml_file = output_dir / 'geological_graph.graphml'
        # Remove mention lists before saving to GraphML (not serializable)
        graph_copy = self.graph.copy()
        for node in graph_copy.nodes():
            if 'mentions' in graph_copy.nodes[node]:
                graph_copy.nodes[node]['mention_count'] = len(graph_copy.nodes[node]['mentions'])
                del graph_copy.nodes[node]['mentions']
        
        nx.write_graphml(graph_copy, graphml_file)
        print(f"✓ Saved GraphML: {graphml_file}")
        
        # Save entity catalog
        entity_file = output_dir / 'entity_catalog.json'
        entities_serializable = {k: list(v) for k, v in self.entities.items()}
        
        with open(entity_file, 'w', encoding='utf-8') as f:
            json.dump(entities_serializable, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved entity catalog: {entity_file}")
        
        # Create summary
        self.create_graph_summary(output_dir)
    
    def create_graph_summary(self, output_dir):
        """Create a human-readable summary of the graph"""
        
        summary_file = output_dir / 'graph_summary.md'
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('# Geological Knowledge Graph Summary\n\n')
            
            f.write(f'## Graph Statistics\n\n')
            f.write(f'- **Total Nodes:** {self.graph.number_of_nodes()}\n')
            f.write(f'- **Total Relationships:** {self.graph.number_of_edges()}\n\n')
            
            f.write(f'## Entity Types\n\n')
            for entity_type, entities in self.entities.items():
                f.write(f'### {entity_type.title()} ({len(entities)})\n\n')
                for entity in sorted(entities):
                    f.write(f'- {entity}\n')
                f.write('\n')
            
            f.write(f'## Most Connected Entities\n\n')
            # Find nodes with most connections
            degree_dict = dict(self.graph.degree())
            top_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:10]
            
            for node_id, degree in top_nodes:
                node_data = self.graph.nodes[node_id]
                f.write(f'- **{node_data.get("name", node_id)}** ({degree} connections)\n')
        
        print(f"✓ Saved graph summary: {summary_file}")


def main():
    """Main execution"""
    
    data_dir = r'c:\cod\licenta\knowledge_extracted'
    output_dir = r'c:\cod\licenta\knowledge_graph'
    
    builder = GeologicalGraphBuilder()
    
    # Build the graph
    success = builder.build_graph(data_dir)
    
    if success:
        # Save graph
        builder.save_graph(output_dir)
        
        print("\n" + "="*80)
        print("✅ KNOWLEDGE GRAPH BUILT SUCCESSFULLY!")
        print("="*80)
        print(f"\nGraph contains:")
        print(f"  • {builder.graph.number_of_nodes()} geological entities")
        print(f"  • {builder.graph.number_of_edges()} relationships")
        print(f"\nNext steps:")
        print(f"  1. Integrate with LLM for Q&A")
        print(f"  2. Build query interface")
        print(f"  3. Add visualization")


if __name__ == "__main__":
    main()
