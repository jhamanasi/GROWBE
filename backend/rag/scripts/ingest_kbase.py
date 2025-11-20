"""
Knowledge Base Ingestion Script.

This script processes JSONL knowledge bases, generates embeddings,
and stores them in LanceDB for vector search.
"""

import json
import lancedb
from pathlib import Path
from typing import List, Dict, Any


def ingest_precurated_jsonl(kbase_name: str, jsonl_path: str):
    """
    Ingest a pre-curated JSONL knowledge base into LanceDB.
    
    Each line in the JSONL file should be a complete, semantically coherent chunk
    that doesn't require further splitting.
    
    Args:
        kbase_name: Name of the knowledge base (must match metadata.json)
        jsonl_path: Path to the .jsonl file
    """
    print(f"\n{'='*60}")
    print(f"📚 Ingesting Knowledge Base: {kbase_name}")
    print(f"{'='*60}\n")
    
    # Load metadata (use absolute path from script location)
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parents[1]
    kbase_dir = backend_dir / "rag" / "knowledge_bases" / kbase_name
    metadata_path = kbase_dir / "metadata.json"
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    print(f"📋 Knowledge Base: {metadata['name']}")
    print(f"📝 Description: {metadata['description'][:100]}...")
    print(f"🎯 Topics: {', '.join(metadata['topics'][:5])}...")
    print(f"🤖 Embedding Model: {metadata['embedding_model']}\n")
    
    # Load JSONL data
    print(f"📖 Reading {jsonl_path}...")
    chunks = []
    
    with open(jsonl_path) as f:
        for line_num, line in enumerate(f, 1):
            try:
                item = json.loads(line)
                
                # Validate required fields
                required = ['chunk_id', 'topic', 'content', 'citations']
                missing = [k for k in required if k not in item]
                if missing:
                    print(f"⚠️  Skipping line {line_num}: missing fields {missing}")
                    continue
                
                chunks.append({
                    'id': item['chunk_id'],
                    'content': item['content'],
                    'metadata': {
                        'chunk_id': item['chunk_id'],
                        'topic': item.get('topic'),
                        'subtopic': item.get('subtopic'),
                        'title': item.get('title'),
                        'keywords': item.get('keywords', []),
                        'kbase': kbase_name
                    },
                    'citations': item['citations']
                })
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping line {line_num}: invalid JSON - {e}")
    
    print(f"✅ Loaded {len(chunks)} chunks\n")
    
    if not chunks:
        print("❌ No valid chunks found. Aborting ingestion.")
        return
    
    # Generate embeddings
    print(f"🔄 Generating embeddings using {metadata['embedding_model']}...")
    print(f"   This may take a moment...\n")
    
    from rag.embedder import embed_batch
    
    texts = [c['content'] for c in chunks]
    embeddings = embed_batch(texts, model=metadata['embedding_model'])
    
    print(f"\n✅ Generated {len(embeddings)} embeddings\n")
    
    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk['vector'] = embedding  # LanceDB expects 'vector' field
    
    # Save to LanceDB
    print(f"💾 Saving to vector database...")
    vector_db_path = backend_dir / "rag" / "vector_db"
    db = lancedb.connect(str(vector_db_path))
    
    # Drop existing table if it exists
    if kbase_name in db.table_names():
        print(f"   Dropping existing table '{kbase_name}'...")
        db.drop_table(kbase_name)
    
    # Create new table
    table = db.create_table(kbase_name, data=chunks, mode="overwrite")
    
    print(f"✅ Created table '{kbase_name}' with {len(chunks)} vectors\n")
    
    # Summary
    print(f"{'='*60}")
    print(f"✅ INGESTION COMPLETE")
    print(f"{'='*60}")
    print(f"Knowledge Base: {kbase_name}")
    print(f"Total Chunks: {len(chunks)}")
    print(f"Embedding Dimension: {len(embeddings[0])}")
    print(f"Table Name: {kbase_name}")
    print(f"Vector DB Path: backend/rag/vector_db")
    print(f"{'='*60}\n")


def test_search(kbase_name: str, test_query: str = "What is credit utilization?"):
    """
    Test search functionality after ingestion.
    
    Args:
        kbase_name: Name of the knowledge base to test
        test_query: Query to test with
    """
    print(f"\n{'='*60}")
    print(f"🔍 Testing Search: {kbase_name}")
    print(f"{'='*60}\n")
    print(f"Query: {test_query}\n")
    
    from rag.kbase_manager import KnowledgeBaseManager
    
    manager = KnowledgeBaseManager()
    results = manager.search(test_query, knowledge_base=kbase_name, top_k=3)
    
    if not results:
        print("❌ No results found\n")
        return
    
    print(f"✅ Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Similarity: {result['similarity_score']:.3f}")
        print(f"  Title: {result['metadata'].get('title', 'N/A')}")
        print(f"  Topic: {result['metadata'].get('topic', 'N/A')}")
        print(f"  Content: {result['content'][:150]}...")
        print(f"  Citations: {result['citations'][:2]}")
        print()


if __name__ == "__main__":
    """
    Main execution: Ingest the financial_concepts knowledge base.
    """
    import sys
    import os
    from dotenv import load_dotenv
    
    # Add backend to path so imports work
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    
    # Load environment variables
    backend_dir = Path(__file__).resolve().parents[2]  # Go up to backend/
    env_path = backend_dir / ".env"
    load_dotenv(env_path)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print(f"   Looking for .env at: {env_path}")
        sys.exit(1)
    
    # Ingest financial concepts
    try:
        # Get absolute paths
        script_dir = Path(__file__).resolve().parent
        backend_dir = script_dir.parents[1]
        jsonl_path = backend_dir / "rag" / "knowledge_bases" / "financial_concepts" / "financial_Kbase.jsonl"
        
        ingest_precurated_jsonl(
            kbase_name="financial_concepts",
            jsonl_path=str(jsonl_path)
        )
        
        # Test search
        test_search(
            kbase_name="financial_concepts",
            test_query="What is the debt avalanche method?"
        )
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

