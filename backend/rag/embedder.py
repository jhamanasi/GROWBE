"""
Embedding generation using OpenAI API.

This module provides utilities for generating text embeddings
using OpenAI's embedding models.
"""

import os
from typing import List
from openai import OpenAI


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def embed_text(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Text to embed
        model: OpenAI embedding model to use
        
    Returns:
        List of floats representing the embedding vector
        
    Raises:
        ValueError: If text is empty
        Exception: If OpenAI API call fails
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    try:
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        raise


def embed_batch(
    texts: List[str], 
    model: str = "text-embedding-3-small",
    batch_size: int = 100
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batches.
    
    OpenAI's embedding API supports up to 2048 texts per request,
    but we use smaller batches for reliability.
    
    Args:
        texts: List of texts to embed
        model: OpenAI embedding model to use
        batch_size: Number of texts to embed per API call
        
    Returns:
        List of embedding vectors (one per input text)
        
    Raises:
        ValueError: If texts list is empty
        Exception: If OpenAI API call fails
    """
    if not texts:
        raise ValueError("Texts list cannot be empty")
    
    all_embeddings = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            response = client.embeddings.create(
                input=batch,
                model=model
            )
            
            # Extract embeddings in the same order
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            
            print(f"✅ Embedded batch {i // batch_size + 1} ({len(batch)} texts)")
            
        except Exception as e:
            print(f"❌ Error embedding batch {i // batch_size + 1}: {e}")
            raise
    
    return all_embeddings


def get_embedding_dimension(model: str = "text-embedding-3-small") -> int:
    """
    Get the dimension of embeddings for a given model.
    
    Args:
        model: OpenAI embedding model name
        
    Returns:
        Dimension of the embedding vectors
    """
    model_dimensions = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    return model_dimensions.get(model, 1536)

