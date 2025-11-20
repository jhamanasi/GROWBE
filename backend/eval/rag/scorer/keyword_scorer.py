"""
Keyword Scorer for Growbe Evaluation Harness

Computes keyword overlap between generated responses and expected answers.
"""

import re
from typing import Dict, Any, List, Set
from collections import Counter
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from eval.rag.config import config


class KeywordScorer:
    """Scorer for keyword overlap between responses and expected answers."""

    def __init__(self):
        """Initialize the keyword scorer."""
        self.min_overlap = config["keyword"]["min_overlap"]
        self.case_sensitive = config["keyword"]["case_sensitive"]
        print("✅ Keyword Scorer initialized")

    def extract_keywords(self, text: str) -> Set[str]:
        """
        Extract keywords from text.

        Args:
            text: Input text

        Returns:
            Set of keywords
        """
        if not text.strip():
            return set()

        # Convert to lower case if not case sensitive
        if not self.case_sensitive:
            text = text.lower()

        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', text)

        # Filter out common stop words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }

        keywords = {word for word in words if len(word) > 2 and word not in stop_words}

        return keywords

    def compute_keyword_overlap(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Compute keyword overlap between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Dictionary with overlap statistics
        """
        keywords1 = self.extract_keywords(text1)
        keywords2 = self.extract_keywords(text2)

        if not keywords1 and not keywords2:
            return {
                "overlap_ratio": 0.0,
                "common_keywords": [],
                "unique_to_text1": [],
                "unique_to_text2": [],
                "total_keywords_1": 0,
                "total_keywords_2": 0
            }

        # Find intersection and differences
        common = keywords1.intersection(keywords2)
        unique1 = keywords1 - keywords2
        unique2 = keywords2 - keywords1

        # Calculate overlap ratio (Jaccard similarity)
        union = keywords1.union(keywords2)
        overlap_ratio = len(common) / len(union) if union else 0.0

        return {
            "overlap_ratio": round(overlap_ratio, 3),
            "common_keywords": sorted(list(common)),
            "unique_to_text1": sorted(list(unique1)),
            "unique_to_text2": sorted(list(unique2)),
            "total_keywords_1": len(keywords1),
            "total_keywords_2": len(keywords2)
        }

    def score_response(self, response: str, expected_answer: str) -> Dict[str, Any]:
        """
        Score a single response against the expected answer.

        Args:
            response: Generated response text
            expected_answer: Expected correct answer

        Returns:
            Dictionary with keyword overlap score and metadata
        """
        overlap_info = self.compute_keyword_overlap(response, expected_answer)

        # Determine if response passes minimum overlap threshold
        passed = overlap_info["overlap_ratio"] >= self.min_overlap

        result = {
            "keyword_score": overlap_info["overlap_ratio"],
            "min_overlap": self.min_overlap,
            "passed": passed,
            "scorer": "keyword",
            "overlap_details": overlap_info
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

        print(f"🔍 Computing keyword overlap scores for {total} response pairs...")

        for i, (response, expected) in enumerate(zip(responses, expected_answers), 1):
            score_result = self.score_response(response, expected)
            results.append(score_result)

            if i % 10 == 0 or i == total:
                passed_count = sum(1 for r in results[-10:] if r.get("passed", False))
                print(f"📊 Keyword scoring: {i}/{total} completed ({passed_count}/10 recent passed)")

        passed_total = sum(1 for r in results if r.get("passed", False))
        avg_score = sum(r.get("keyword_score", 0) for r in results) / len(results)

        print(f"✅ Keyword scoring complete: {passed_total}/{total} passed (avg: {avg_score:.3f})")

        return results


# Test function
if __name__ == "__main__":
    scorer = KeywordScorer()

    # Test examples
    test_cases = [
        {
            "response": "The debt snowball method focuses on paying off smallest debts first for psychological motivation.",
            "expected": "Debt snowball pays off smallest balances first to build momentum and motivation."
        },
        {
            "response": "Credit cards are plastic money that you can use to buy things.",
            "expected": "Credit cards allow borrowing money up to a limit and require monthly payments."
        }
    ]

    print("\n" + "="*60)
    print("KEYWORD SCORER TEST")
    print("="*60)

    for i, test_case in enumerate(test_cases, 1):
        result = scorer.score_response(test_case["response"], test_case["expected"])

        print(f"\nTest Case {i}:")
        print(f"Response: {test_case['response'][:80]}...")
        print(f"Expected: {test_case['expected'][:80]}...")
        print(f"Keyword Overlap: {result['keyword_score']} (Min: {result['min_overlap']})")
        print(f"Common Keywords: {result['overlap_details']['common_keywords'][:5]}...")
        print(f"Passed: {result['passed']}")
