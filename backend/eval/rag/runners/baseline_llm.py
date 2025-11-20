"""
Baseline LLM Runner for Growbe Evaluation Harness

Generates responses using only the LLM without RAG context, using client.responses.create().
This serves as the baseline for comparing RAG performance.
"""

import os
import sys
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=backend_dir / '.env')

# Add backend to path for imports
sys.path.insert(0, str(backend_dir))

from openai import OpenAI

from eval.rag.config import config


class BaselineLLMRunner:
    """Runner for baseline LLM responses (without RAG)."""

    def __init__(self):
        """Initialize the baseline LLM runner with OpenAI client."""
        self.client = OpenAI(api_key=config["openai"]["api_key"])
        self.model = config["openai"]["model"]
        self.max_tokens = config["openai"]["max_tokens"]
        self.temperature = config["openai"]["temperature"]

        print("✅ Baseline LLM Runner initialized")

    def build_baseline_prompt(self, query: str) -> str:
        """
        Build the baseline prompt without RAG context.

        Args:
            query: User's question

        Returns:
            Prompt for the LLM using only general knowledge
        """
        prompt = f"""You are Growbe, a helpful AI financial advisor.

QUESTION: {query}

Provide a clear, accurate answer using your financial knowledge."""

        return prompt

    def generate_response(self, query: str) -> Dict[str, Any]:
        """
        Generate a baseline LLM response for the given query (no RAG).

        Args:
            query: The user's question

        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Build baseline prompt
            prompt = self.build_baseline_prompt(query)

            # Call OpenAI API using client.responses.create()
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
                "context_used": False,
                "context_length": 0,
                "model": self.model,
                "temperature": self.temperature,
                "method": "baseline",
                "success": True
            }

            print(f"✅ Baseline response generated ({len(response_text)} chars)")
            return result

        except Exception as e:
            print(f"❌ Error generating baseline response: {e}")
            return {
                "query": query,
                "response": "",
                "error": str(e),
                "context_used": False,
                "context_length": 0,
                "model": self.model,
                "method": "baseline",
                "success": False
            }

    def run_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Generate baseline responses for a batch of queries.

        Args:
            queries: List of user questions

        Returns:
            List of response dictionaries
        """
        results = []
        total_queries = len(queries)

        print(f"🚀 Starting baseline batch processing of {total_queries} queries...")

        for i, query in enumerate(queries, 1):
            print(f"📝 Processing query {i}/{total_queries}: {query[:50]}...")

            result = self.generate_response(query)
            results.append(result)

            # Progress indicator
            if i % 10 == 0 or i == total_queries:
                success_count = sum(1 for r in results[-10:] if r.get("success", False))
                print(f"📊 Progress: {i}/{total_queries} completed ({success_count}/10 recent successful)")

        successful_responses = sum(1 for r in results if r.get("success", False))
        print(f"✅ Baseline batch complete: {successful_responses}/{total_queries} successful responses")

        return results


# Standalone runner for testing
if __name__ == "__main__":
    runner = BaselineLLMRunner()

    # Test query
    test_query = "What is the difference between debt snowball and debt avalanche methods?"
    result = runner.generate_response(test_query)

    print("\n" + "="*50)
    print("BASELINE RESPONSE TEST")
    print("="*50)
    print(f"Query: {result['query']}")
    print(f"Response: {result['response'][:200]}...")
    print(f"Context Used: {result['context_used']}")
    print(f"Success: {result['success']}")
