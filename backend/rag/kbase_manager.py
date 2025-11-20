"""
Knowledge Base Manager for multi-Kbase RAG system.

This module handles:
- Loading metadata for all knowledge bases
- Routing queries to appropriate knowledge bases
- Vector search in LanceDB
- Merging and ranking results from multiple Kbases
"""

import json
import lancedb
from typing import List, Dict, Optional, Any
from pathlib import Path


class KnowledgeBaseManager:
    """Manages multiple knowledge bases and routes queries intelligently."""
    
    def __init__(self, vector_db_path: str = "backend/rag/vector_db"):
        """
        Initialize the Knowledge Base Manager.
        
        Args:
            vector_db_path: Path to LanceDB database directory
        """
        self.vector_db_path = Path(vector_db_path)
        self.db = lancedb.connect(str(self.vector_db_path))
        self.kbases = self._load_metadata()
        
        print(f"📚 Loaded {len(self.kbases)} knowledge bases")
        for name, meta in self.kbases.items():
            print(f"  • {name}: {meta.get('description', 'No description')[:80]}...")
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """
        Load metadata for all knowledge bases.
        
        Returns:
            Dictionary mapping Kbase name to metadata
        """
        kbases = {}
        # Use absolute path from this file's location
        kbase_dir = Path(__file__).resolve().parent / "knowledge_bases"
        
        if not kbase_dir.exists():
            print(f"⚠️  Knowledge base directory not found: {kbase_dir}")
            return kbases
        
        for kbase_path in kbase_dir.iterdir():
            if kbase_path.is_dir():
                meta_file = kbase_path / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file) as f:
                            metadata = json.load(f)
                            kbases[metadata['name']] = metadata
                    except Exception as e:
                        print(f"⚠️  Error loading metadata for {kbase_path.name}: {e}")
        
        return kbases
    
    def search(
        self, 
        query: str, 
        knowledge_base: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge bases for relevant information.
        
        Args:
            query: User's question or search query
            knowledge_base: Specific Kbase name (optional, will auto-route if not provided)
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata and similarity scores
        """
        from rag.embedder import embed_text
        
        # Generate query embedding
        try:
            query_embedding = embed_text(query)
        except Exception as e:
            print(f"❌ Error embedding query: {e}")
            return []
        
        # If specific Kbase requested, search only that
        if knowledge_base:
            if knowledge_base not in self.kbases:
                print(f"⚠️  Knowledge base '{knowledge_base}' not found")
                return []
            return self._search_single_kbase(
                knowledge_base, query, query_embedding, top_k
            )
        
        # Otherwise, intelligently route based on query + metadata
        relevant_kbases = self._route_query_to_kbases(query)
        
        if not relevant_kbases:
            print(f"⚠️  No relevant knowledge bases found for query: {query[:50]}...")
            return []
        
        # Search all relevant Kbases and merge results
        all_results = []
        for kbase_name in relevant_kbases:
            results = self._search_single_kbase(
                kbase_name, query, query_embedding, top_k
            )
            all_results.extend(results)
        
        # Re-rank and return top_k across all Kbases
        all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return all_results[:top_k]
    
    def _route_query_to_kbases(self, query: str) -> List[str]:
        """
        Determine which Kbases are relevant for this query.
        
        Uses keyword matching on topics and description.
        
        Args:
            query: User's search query
            
        Returns:
            List of Kbase names, sorted by priority
        """
        query_lower = query.lower()
        relevant_kbases = []
        
        # Check each Kbase's topics and description
        for kbase_name, metadata in self.kbases.items():
            # Skip web-search Kbases (they have special handling)
            if metadata.get('use_web_search', False):
                continue
            
            # Check if query mentions any topics
            topics = metadata.get('topics', [])
            topic_match = any(
                topic.lower().replace('_', ' ') in query_lower 
                for topic in topics
            )
            
            # Check if query matches description keywords
            description = metadata.get('description', '').lower()
            desc_keywords = [
                'credit', 'debt', 'loan', 'mortgage', 'interest', 
                'apr', 'score', 'dti', 'amortization', 'refinance',
                'student', 'housing', 'rent', 'buy'
            ]
            desc_match = any(
                keyword in query_lower and keyword in description
                for keyword in desc_keywords
            )
            
            if topic_match or desc_match:
                relevant_kbases.append((kbase_name, metadata['priority']))
        
        # If no matches, include all non-web-search Kbases
        if not relevant_kbases:
            relevant_kbases = [
                (name, meta['priority']) 
                for name, meta in self.kbases.items() 
                if not meta.get('use_web_search', False)
            ]
        
        # Sort by priority (lower number = higher priority)
        relevant_kbases.sort(key=lambda x: x[1])
        
        return [name for name, _ in relevant_kbases]
    
    def _search_single_kbase(
        self, 
        kbase_name: str, 
        query: str, 
        query_embedding: List[float], 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Search a specific knowledge base.
        
        Args:
            kbase_name: Name of the knowledge base
            query: Original query text
            query_embedding: Embedded query vector
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        metadata = self.kbases.get(kbase_name)
        if not metadata:
            return []
        
        # Check if this is a web-search Kbase
        if metadata.get('use_web_search'):
            # TODO: Implement web search with caching
            print(f"⚠️  Web search not yet implemented for {kbase_name}")
            return []
        
        # Check if table exists in LanceDB
        if kbase_name not in self.db.table_names():
            print(f"⚠️  Table '{kbase_name}' not found in vector database")
            return []
        
        # Vector search in LanceDB
        try:
            table = self.db.open_table(kbase_name)
            results = table.search(query_embedding).limit(top_k).to_list()
            
            # Filter by similarity threshold
            threshold = metadata['retrieval_params'].get('similarity_threshold', 0.7)
            filtered_results = []
            
            for r in results:
                # LanceDB uses distance, convert to similarity (1 - distance)
                similarity = 1 - r.get('_distance', 1.0)
                
                if similarity >= threshold:
                    filtered_results.append({
                        'content': r.get('content', ''),
                        'metadata': r.get('metadata', {}),
                        'similarity_score': similarity,
                        'source': kbase_name,
                        'citations': r.get('citations', [])
                    })
            
            return filtered_results
            
        except Exception as e:
            print(f"❌ Error searching {kbase_name}: {e}")
            return []
    
    def list_kbases(self) -> List[str]:
        """List all available knowledge base names."""
        return list(self.kbases.keys())
    
    def get_kbase_info(self, kbase_name: str) -> Optional[Dict]:
        """Get metadata for a specific knowledge base."""
        return self.kbases.get(kbase_name)

