"""
Similarity Scorer for Growbe Evaluation Harness

Uses Sentence Transformers to compute semantic similarity between
generated responses and expected answers.
"""

from typing import Dict, Any, Tuple
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from eval.rag.config import config


class SimilarityScorer:
    """Scorer for semantic similarity between responses and expected answers."""

    def __init__(self):
        """Initialize the similarity scorer with simple text similarity."""
        # Using simple word-based similarity to avoid TensorFlow/Keras issues
        self.threshold = config["similarity"]["threshold"]
        self.use_simple_method = True
        print("✅ Similarity Scorer initialized (using simple word similarity)")

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts using simple word similarity.

        Args:
            text1: First text to compare
            text2: Second text to compare

        Returns:
            Similarity score between 0 and 1
        """
        return self._simple_similarity(text1, text2)

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """
        Simple text similarity using Jaccard similarity of words.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        import re
        from collections import Counter

        # Convert to lowercase and split into words
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))

        if not words1 and not words2:
            return 1.0 if text1.strip() == text2.strip() else 0.0

        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        if union == 0:
            return 0.0

        return round(intersection / union, 3)

    def score_response(self, response: str, expected_answer: str) -> Dict[str, Any]:
        """
        Score a single response against the expected answer.

        Args:
            response: Generated response text
            expected_answer: Expected correct answer

        Returns:
            Dictionary with similarity score and metadata
        """
        similarity_score = self.compute_similarity(response, expected_answer)

        # Determine if response passes threshold
        passed = similarity_score >= self.threshold

        result = {
            "similarity_score": similarity_score,
            "threshold": self.threshold,
            "passed": passed,
            "scorer": "similarity"
        }

        return result

    def score_batch(self, responses: list, expected_answers: list) -> list:
        """
        Score a batch of responses.

        Args:
            responses: List of generated response texts
            expected_answers: List of expected answer texts

        Returns:
            List of score dictionaries
        """
        if len(responses) != len(expected_answers):
            raise ValueError("Responses and expected answers must have same length")

        results = []
        total = len(responses)

        print(f"🔍 Computing similarity scores for {total} response pairs...")

        for i, (response, expected) in enumerate(zip(responses, expected_answers), 1):
            score_result = self.score_response(response, expected)
            results.append(score_result)

            if i % 10 == 0 or i == total:
                passed_count = sum(1 for r in results[-10:] if r.get("passed", False))
                print(f"📊 Similarity scoring: {i}/{total} completed ({passed_count}/10 recent passed)")

        passed_total = sum(1 for r in results if r.get("passed", False))
        avg_score = sum(r.get("similarity_score", 0) for r in results) / len(results)

        print(f"✅ Similarity scoring complete: {passed_total}/{total} passed (avg: {avg_score:.3f})")

        return results


# Test function
if __name__ == "__main__":
    scorer = SimilarityScorer()

    # Test examples
    test_cases = [
        {
            "response": "The debt snowball method focuses on paying off smallest debts first for psychological motivation.",
            "expected": "Debt snowball pays off smallest balances first to build momentum and motivation."
        },
        {
            "response": "Credit cards are plastic money.",
            "expected": "Credit cards allow borrowing money up to a limit and require monthly payments."
        }
    ]

    print("\n" + "="*60)
    print("SIMILARITY SCORER TEST")
    print("="*60)

    for i, test_case in enumerate(test_cases, 1):
        result = scorer.score_response(test_case["response"], test_case["expected"])

        print(f"\nTest Case {i}:")
        print(f"Response: {test_case['response'][:80]}...")
        print(f"Expected: {test_case['expected'][:80]}...")
        print(f"Similarity: {result['similarity_score']} (Threshold: {result['threshold']})")
        print(f"Passed: {result['passed']}")
