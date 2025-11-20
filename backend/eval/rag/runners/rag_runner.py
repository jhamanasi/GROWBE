"""
RAG Runner for Growbe Evaluation Harness

Uses the Knowledge Base Manager to retrieve relevant context and then calls
the OpenAI API using client.responses.create() to generate RAG-augmented responses.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=backend_dir / '.env')

# Add backend to path for imports
sys.path.insert(0, str(backend_dir))

from openai import OpenAI
from rag.kbase_manager import KnowledgeBaseManager

from eval.rag.config import config


class RAGRunner:
    """Runner for RAG-augmented LLM responses."""

    def __init__(self):
        """Initialize the RAG runner with OpenAI client and knowledge base manager."""
        self.client = OpenAI(api_key=config["openai"]["api_key"])
        self.model = config["openai"]["model"]
        self.max_tokens = config["openai"]["max_tokens"]
        self.temperature = config["openai"]["temperature"]

        # Initialize knowledge base manager
        # Path relative to the main backend directory
        kbase_path = backend_dir / "rag" / "vector_db"
        self.kbase_manager = KnowledgeBaseManager(str(kbase_path))

        # RAG configuration
        self.top_k_chunks = config["rag"]["top_k_chunks"]
        self.max_context_length = config["rag"]["max_context_length"]
        self.knowledge_base = config["rag"]["knowledge_base"]

        print("✅ RAG Runner initialized")

    def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context from knowledge base.

        Args:
            query: The user's question

        Returns:
            Formatted context string for the LLM
        """
        try:
            # Search knowledge base
            results = self.kbase_manager.search(
                query=query,
                knowledge_base=self.knowledge_base,
                top_k=self.top_k_chunks
            )

            if not results:
                print(f"⚠️ No context found for query: {query[:50]}...")
                return ""

            # Format context from results
            context_parts = []
            for result in results:
                chunk_text = result.get("content", "").strip()
                if chunk_text:
                    # Truncate if too long
                    if len(chunk_text) > 500:
                        chunk_text = chunk_text[:500] + "..."
                    context_parts.append(chunk_text)

            context = "\n\n".join(context_parts)

            # Truncate overall context if needed
            if len(context) > self.max_context_length:
                context = context[:self.max_context_length] + "..."

            print(f"📚 Retrieved {len(results)} chunks, {len(context)} chars of context")
            return context

        except Exception as e:
            print(f"❌ Error retrieving context: {e}")
            return ""

    def build_rag_prompt(self, query: str, context: str) -> str:
        """
        Build the RAG-augmented prompt.

        Args:
            query: User's question
            context: Retrieved context

        Returns:
            Complete prompt for the LLM
        """
        if context:
            prompt = f"""You are Growbe, a helpful AI financial advisor.

Use the following context to help answer the user's question accurately. If the context doesn't contain relevant information, use your general financial knowledge but prioritize the provided context.

CONTEXT:
{context}

QUESTION: {query}

Provide a clear, accurate answer based on the context above."""
        else:
            # Fallback prompt when no context is available
            prompt = f"""You are Growbe, a helpful AI financial advisor.

QUESTION: {query}

Provide a clear, accurate answer using your financial knowledge."""

        return prompt

    def generate_response(self, query: str) -> Dict[str, Any]:
        """
        Generate a RAG-augmented response for the given query.

        Args:
            query: The user's question

        Returns:
            Dictionary containing response, context, and metadata
        """
        try:
            # Step 1: Retrieve context
            context = self.retrieve_context(query)

            # Step 2: Build RAG prompt
            prompt = self.build_rag_prompt(query, context)

            # Step 3: Call OpenAI API using client.responses.create()
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
                truncation="auto"
            )

            # Extract the response text
            response_text = ""
            if response.output and len(response.output) > 0:
                # Get the first output item (should be text)
                first_output = response.output[0]
                if hasattr(first_output, 'content') and first_output.content:
                    response_text = first_output.content[0].text if hasattr(first_output.content[0], 'text') else str(first_output.content[0])

            result = {
                "query": query,
                "response": response_text,
                "context_used": bool(context),
                "context_length": len(context),
                "model": self.model,
                "temperature": self.temperature,
                "method": "rag",
                "success": True
            }

            print(f"✅ RAG response generated ({len(response_text)} chars)")
            return result

        except Exception as e:
            print(f"❌ Error generating RAG response: {e}")
            return {
                "query": query,
                "response": "",
                "error": str(e),
                "context_used": False,
                "context_length": 0,
                "model": self.model,
                "method": "rag",
                "success": False
            }

    def run_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Generate RAG responses for a batch of queries.

        Args:
            queries: List of user questions

        Returns:
            List of response dictionaries
        """
        results = []
        total_queries = len(queries)

        print(f"🚀 Starting RAG batch processing of {total_queries} queries...")

        for i, query in enumerate(queries, 1):
            print(f"📝 Processing query {i}/{total_queries}: {query[:50]}...")

            result = self.generate_response(query)
            results.append(result)

            # Progress indicator
            if i % 10 == 0 or i == total_queries:
                success_count = sum(1 for r in results[-10:] if r.get("success", False))
                print(f"📊 Progress: {i}/{total_queries} completed ({success_count}/10 recent successful)")

        successful_responses = sum(1 for r in results if r.get("success", False))
        print(f"✅ RAG batch complete: {successful_responses}/{total_queries} successful responses")

        return results


# Standalone runner for testing
if __name__ == "__main__":
    runner = RAGRunner()

    # Test query
    test_query = "What is the difference between debt snowball and debt avalanche methods?"
    result = runner.generate_response(test_query)

    print("\n" + "="*50)
    print("RAG RESPONSE TEST")
    print("="*50)
    print(f"Query: {result['query']}")
    print(f"Response: {result['response'][:200]}...")
    print(f"Context Used: {result['context_used']}")
    print(f"Success: {result['success']}")
