"""
Hallucination Scorer for Growbe Evaluation Harness

Detects potential hallucinations in generated responses by checking for
factual inconsistencies and unsupported claims.
"""

import re
from typing import Dict, Any, List
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from eval.rag.config import config


class HallucinationScorer:
    """Scorer for detecting hallucinations in responses."""

    def __init__(self):
        """Initialize the hallucination scorer."""
        self.max_confidence_threshold = config["hallucination"]["max_confidence_threshold"]
        self.fact_checking_enabled = config["hallucination"]["fact_checking_enabled"]

        # Define patterns that might indicate hallucinations
        self.hallucination_patterns = {
            "specific_numbers": r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b',  # Specific numbers that might be made up
            "specific_percentages": r'\b\d{1,2}(?:\.\d+)?%\b',  # Specific percentages
            "specific_dates": r'\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b',  # Specific dates
            "authoritative_phrases": [
                "according to", "studies show", "research indicates", "experts agree",
                "data shows", "statistics prove", "industry standard", "best practice"
            ]
        }

        # Financial facts that should be accurate
        self.financial_facts = {
            "debt_snowball_vs_avalanche": ["snowball", "avalanche", "smallest", "highest"],
            "credit_score_range": ["300", "850"],
            "emergency_fund_months": ["3", "6"],
            "retirement_contribution_2024": ["23,000"],
        }

        print("✅ Hallucination Scorer initialized")

    def detect_specific_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect specific claims that might be hallucinations.

        Args:
            text: Response text to analyze

        Returns:
            List of detected claims with confidence scores
        """
        claims = []

        # Check for specific numbers
        numbers = re.findall(self.hallucination_patterns["specific_numbers"], text)
        for number in numbers:
            # Skip common numbers that are likely accurate
            if number in ["0", "1", "2", "3", "6", "12", "30", "100"]:
                continue
            claims.append({
                "type": "specific_number",
                "value": number,
                "confidence": 0.7,  # High confidence for made-up numbers
                "reason": "Specific numbers often indicate fabricated data"
            })

        # Check for specific percentages
        percentages = re.findall(self.hallucination_patterns["specific_percentages"], text)
        for percentage in percentages:
            claims.append({
                "type": "specific_percentage",
                "value": percentage,
                "confidence": 0.6,
                "reason": "Specific percentages without sources may be inaccurate"
            })

        # Check for specific dates
        dates = re.findall(self.hallucination_patterns["specific_dates"], text)
        for date in dates:
            claims.append({
                "type": "specific_date",
                "value": date,
                "confidence": 0.8,
                "reason": "Specific dates without context may be fabricated"
            })

        # Check for authoritative phrases without sources
        for phrase in self.hallucination_patterns["authoritative_phrases"]:
            if phrase.lower() in text.lower():
                # Check if there's a source citation nearby
                context_start = max(0, text.lower().find(phrase.lower()) - 50)
                context_end = min(len(text), text.lower().find(phrase.lower()) + len(phrase) + 50)
                context = text[context_start:context_end]

                has_source = any(word in context.lower() for word in ["source", "study", "research", "according"])
                if not has_source:
                    claims.append({
                        "type": "authoritative_claim",
                        "value": phrase,
                        "confidence": 0.5,
                        "reason": "Authoritative claims without sources may be unsupported"
                    })

        return claims

    def check_financial_accuracy(self, text: str, expected_answer: str) -> List[Dict[str, Any]]:
        """
        Check for financial inaccuracies.

        Args:
            text: Response text
            expected_answer: Expected correct answer

        Returns:
            List of potential inaccuracies
        """
        inaccuracies = []

        # Simple check: if key terms from expected answer are missing from response
        expected_keywords = set(expected_answer.lower().split())
        response_keywords = set(text.lower().split())

        missing_key_terms = expected_keywords - response_keywords
        if len(missing_key_terms) > 3:  # Too many key terms missing
            inaccuracies.append({
                "type": "missing_key_information",
                "confidence": 0.4,
                "reason": f"Missing key terms: {list(missing_key_terms)[:5]}..."
            })

        return inaccuracies

    def compute_hallucination_score(self, response: str, expected_answer: str = "") -> Dict[str, Any]:
        """
        Compute hallucination score for a response.

        Args:
            response: Generated response text
            expected_answer: Expected correct answer (optional)

        Returns:
            Dictionary with hallucination analysis
        """
        claims = self.detect_specific_claims(response)

        if expected_answer:
            inaccuracies = self.check_financial_accuracy(response, expected_answer)
            claims.extend(inaccuracies)

        # Calculate overall hallucination confidence
        if not claims:
            hallucination_confidence = 0.0
        else:
            # Average confidence of all detected claims
            hallucination_confidence = sum(claim["confidence"] for claim in claims) / len(claims)
            hallucination_confidence = round(hallucination_confidence, 3)

        # Determine if response is likely hallucinating
        is_hallucinating = hallucination_confidence >= self.max_confidence_threshold

        return {
            "hallucination_score": hallucination_confidence,
            "threshold": self.max_confidence_threshold,
            "is_hallucinating": is_hallucinating,
            "detected_claims": claims,
            "claims_count": len(claims)
        }

    def score_response(self, response: str, expected_answer: str = "") -> Dict[str, Any]:
        """
        Score a single response for hallucinations.

        Args:
            response: Generated response text
            expected_answer: Expected correct answer

        Returns:
            Dictionary with hallucination score and metadata
        """
        hallucination_info = self.compute_hallucination_score(response, expected_answer)

        result = {
            "hallucination_score": hallucination_info["hallucination_score"],
            "threshold": hallucination_info["threshold"],
            "passed": not hallucination_info["is_hallucinating"],  # Pass if NOT hallucinating
            "scorer": "hallucination",
            "hallucination_details": hallucination_info
        }

        return result

    def score_batch(self, responses: list, expected_answers: list = None) -> list:
        """
        Score a batch of responses for hallucinations.

        Args:
            responses: List of generated response texts
            expected_answers: List of expected answer texts (optional)

        Returns:
            List of score dictionaries
        """
        if expected_answers and len(responses) != len(expected_answers):
            raise ValueError("Responses and expected answers must have same length")

        if not expected_answers:
            expected_answers = [""] * len(responses)

        results = []
        total = len(responses)

        print(f"🔍 Analyzing hallucinations in {total} responses...")

        for i, (response, expected) in enumerate(zip(responses, expected_answers), 1):
            score_result = self.score_response(response, expected)
            results.append(score_result)

            if i % 10 == 0 or i == total:
                hallucinating_count = sum(1 for r in results[-10:] if r["hallucination_details"]["is_hallucinating"])
                print(f"📊 Hallucination analysis: {i}/{total} completed ({hallucinating_count}/10 recent flagged)")

        hallucinating_total = sum(1 for r in results if r["hallucination_details"]["is_hallucinating"])
        avg_score = sum(r.get("hallucination_score", 0) for r in results) / len(results)

        print(f"✅ Hallucination analysis complete: {hallucinating_total}/{total} flagged (avg score: {avg_score:.3f})")

        return results


# Test function
if __name__ == "__main__":
    scorer = HallucinationScorer()

    # Test examples
    test_cases = [
        {
            "response": "According to a 2023 study, 87% of Americans have $5,000 in emergency savings on March 15, 2024.",
            "expected": "Most financial experts recommend 3-6 months of expenses in an emergency fund."
        },
        {
            "response": "The debt snowball method pays off smallest debts first to build momentum.",
            "expected": "Debt snowball method focuses on psychological motivation by paying smallest balances first."
        }
    ]

    print("\n" + "="*60)
    print("HALLUCINATION SCORER TEST")
    print("="*60)

    for i, test_case in enumerate(test_cases, 1):
        result = scorer.score_response(test_case["response"], test_case["expected"])

        print(f"\nTest Case {i}:")
        print(f"Response: {test_case['response'][:80]}...")
        print(f"Hallucination Score: {result['hallucination_score']} (Threshold: {result['threshold']})")
        print(f"Is Hallucinating: {result['hallucination_details']['is_hallucinating']}")
        print(f"Detected Claims: {result['hallucination_details']['claims_count']}")
        print(f"Passed: {result['passed']}")
