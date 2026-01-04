"""
Simple AI Assistant Interface for Romanian Petroleum Geology
Uses the knowledge graph to answer questions about geological entities and relationships
"""

import pickle
from pathlib import Path
import networkx as nx
import json

class GeologicalAI:
    """AI assistant that knows Romanian petroleum geology"""
    
    def __init__(self, graph_dir):
        """Load the knowledge graph"""
        graph_file = Path(graph_dir) / 'geological_graph.pkl'
        
        with open(graph_file, 'rb') as f:
            self.graph = pickle.load(f)
        
        print(f"✓ Loaded knowledge graph with {self.graph.number_of_nodes()} entities")
        
        # Load entity catalog
        entity_file = Path(graph_dir) / 'entity_catalog.json'
        with open(entity_file, 'r', encoding='utf-8') as f:
            self.entities = json.load(f)
    
    def find_entity(self, search_term):
        """Find entities matching the search term"""
        matches = []
        search_lower = search_term.lower()
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            name = node_data.get('name', '').lower()
            ro_name = node_data.get('romanian_name', '').lower()
            
            if search_lower in name or search_lower in ro_name:
                matches.append({
                    'id': node_id,
                    'name': node_data.get('name'),
                    'romanian_name': node_data.get('romanian_name', ''),
                    'type': node_data.get('type'),
                    'mention_count': len(node_data.get('mentions', []))
                })
        
        return matches
    
    def get_connections(self, entity_id):
        """Get all entities connected to this one"""
        if not self.graph.has_node(entity_id):
            return []
        
        connections = []
        
        # Find all neighbors
        for neighbor in self.graph.neighbors(entity_id):
            neighbor_data = self.graph.nodes[neighbor]
            edge_data = list(self.graph[entity_id][neighbor].values())[0]
            
            connections.append({
                'entity': neighbor_data.get('name', neighbor),
                'type': neighbor_data.get('type'),
                'relationship': edge_data.get('relationship'),
                'weight': edge_data.get('weight', 1)
            })
        
        return sorted(connections, key=lambda x: x['weight'], reverse=True)
    
    def answer_question(self, question):
        """Simple rule-based Q&A using the graph"""
        
        question_lower = question.lower()
        
        # Question type: "what is X?"
        if any(word in question_lower for word in ['what is', 'what are', 'tell me about']):
            # Extract entity name from question
            for entity_type, entity_list in self.entities.items():
                for entity in entity_list:
                    if entity.lower() in question_lower:
                        return self.describe_entity(entity, entity_type)
            
            return "I couldn't identify the entity you're asking about. Try asking about platforms, zones, or rock types."
        
        # Question type: "where is X found?"
        elif any(word in question_lower for word in ['where', 'location', 'found in']):
            return "Location queries require more detailed field data. This feature will be enhanced when the 1979 field catalog is processed."
        
        # List all of type
        elif 'list' in question_lower or 'show me' in question_lower:
            if 'platform' in question_lower:
                return f"Major platforms: {', '.join(self.entities['platforms'])}"
            elif 'zone' in question_lower:
                return f"Known zones: {', '.join(sorted(self.entities['zones']))}"
            elif 'rock' in question_lower:
                return f"Rock types: {', '.join(self.entities['rocks'])}"
        
        return "I can answer questions about platforms, zones, rocks, and their relationships. Try asking 'What is the Moesian Platform?' or 'List all platforms'."
    
    def describe_entity(self, entity_name, entity_type):
        """Describe an entity and its connections"""
        
        # Find node ID
        node_id = None
        for nid in self.graph.nodes():
            if self.graph.nodes[nid].get('name', '').lower() == entity_name.lower():
                node_id = nid
                break
        
        if not node_id:
            return f"I don't have detailed information about {entity_name} yet."
        
        node_data = self.graph.nodes[node_id]
        connections = self.get_connections(node_id)
        
        response = f"**{node_data.get('name')}**\n\n"
        response += f"Type: {node_data.get('type')}\n"
        
        if node_data.get('romanian_name'):
            response += f"Romanian: {node_data.get('romanian_name')}\n"
        
        response += f"Mentioned {len(node_data.get('mentions', []))} times in documents\n\n"
        
        if connections:
            response += f"Related entities:\n"
            for conn in connections[:10]:  # Top 10
                response += f"  - {conn['entity']} ({conn['type']}) - {conn['weight']} co-mentions\n"
        
        return response
    
    def interactive_mode(self):
        """Simple interactive Q&A"""
        
        print("\n" + "="*80)
        print("ROMANIAN PETROLEUM GEOLOGY AI ASSISTANT")
        print("="*80)
        print(f"\nKnowledge base: {self.graph.number_of_nodes()} entities, {self.graph.number_of_edges()} relationships")
        print("\nAsk me questions about Romanian petroleum geology!")
        print("Type 'exit' to quit, 'help' for suggestions\n")
        
        while True:
            try:
                question = input("\n📚 Your question: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye!")
                    break
                
                if question.lower() == 'help':
                    print("\nTry these questions:")
                    print("  - List all platforms")
                    print("  - What is the Moesian Platform?")
                    print("  - Show me all rock types")
                    print("  - Tell me about sandstones")
                    continue
                
                # Answer the question
                answer = self.answer_question(question)
                print(f"\n🤖 Answer:\n{answer}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


def demo_mode():
    """Demonstration mode with preset questions"""
    
    graph_dir = r'c:\cod\licenta\knowledge_graph'
    ai = GeologicalAI(graph_dir)
    
    print("\n" + "="*80)
    print("DEMONSTRATION: AI GEOLOGICAL KNOWLEDGE SYSTEM")
    print("="*80)
    
    demo_questions = [
        "List all platforms",
        "What is hydrocarbons?",
        "Show me all rock types",
        "Tell me about sandstones"
    ]
    
    for question in demo_questions:
        print(f"\n📚 Q: {question}")
        answer = ai.answer_question(question)
        print(f"🤖 A:\n{answer}")
        print("-" * 80)


def main():
    """Main execution"""
    
    import sys
    
    graph_dir = r'c:\cod\licenta\knowledge_graph'
    ai = GeologicalAI(graph_dir)
    
    if '--demo' in sys.argv:
        demo_mode()
    else:
        ai.interactive_mode()


if __name__ == "__main__":
    main()
