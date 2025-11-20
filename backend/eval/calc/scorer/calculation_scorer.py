#!/usr/bin/env python3
"""
Calculation Scorer for Financial Calculations

Scores LLM responses on:
- Numerical accuracy (exact matches within tolerance)
- Calculation correctness (proper formulas/methods)
- Explanation quality (clear step-by-step reasoning)
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from eval.calc.config import config


class CalculationScorer:
    """Scorer for calculation accuracy and quality."""

    def __init__(self):
        self.accuracy_config = config["accuracy"]
        self.calculation_config = config["calculation"]
        self.explanation_config = config["explanation"]
        self.scoring_weights = config["scoring_weights"]

    def score_response(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single LLM response against expected answer.

        Args:
            expected: Expected answer from tool
            actual: LLM response

        Returns:
            Scoring results with breakdown
        """
        scenario_type = expected.get("scenario_type", "unknown")
        llm_response = actual.get("llm_response", "")

        try:
            # Extract key metrics from LLM response
            extracted_metrics = self._extract_metrics_from_response(llm_response, scenario_type)

            # Score each component
            numerical_score = self._score_numerical_accuracy(expected, extracted_metrics)
            calculation_score = self._score_calculation_correctness(llm_response, scenario_type)
            explanation_score = self._score_explanation_quality(llm_response)

            # Calculate weighted total score
            total_score = (
                numerical_score * self.scoring_weights["numerical_accuracy"] +
                calculation_score * self.scoring_weights["calculation_correctness"] +
                explanation_score * self.scoring_weights["explanation_quality"]
            )

            return {
                "question_id": expected["question_id"],
                "scenario_type": scenario_type,
                "total_score": round(total_score, 3),
                "numerical_accuracy": round(numerical_score, 3),
                "calculation_correctness": round(calculation_score, 3),
                "explanation_quality": round(explanation_score, 3),
                "extracted_metrics": extracted_metrics,
                "expected_metrics": self._get_expected_metrics(expected),
                "scoring_breakdown": {
                    "numerical_details": self._get_numerical_scoring_details(expected, extracted_metrics),
                    "calculation_details": self._get_calculation_scoring_details(llm_response, scenario_type),
                    "explanation_details": self._get_explanation_scoring_details(llm_response)
                }
            }

        except Exception as e:
            print(f"❌ Error scoring question {expected.get('question_id', 'unknown')}: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return minimal scoring result on error
            return {
                "question_id": expected.get("question_id", "unknown"),
                "scenario_type": scenario_type,
                "total_score": 0.0,
                "numerical_accuracy": 0.0,
                "calculation_correctness": 0.0,
                "explanation_quality": 0.0,
                "extracted_metrics": {},
                "expected_metrics": {},
                "scoring_breakdown": {},
                "error": str(e)
            }

    def _extract_metrics_from_response(self, response: str, scenario_type: str) -> Dict[str, Any]:
        """Extract key numerical metrics from LLM response."""

        metrics = {}

        try:
            # Extract monetary amounts (dollars)
            money_pattern = r'\$([0-9,]+\.?\d*)'
            money_matches = re.findall(money_pattern, response)
            if money_matches and isinstance(money_matches, list):
                # Convert to float and sort by magnitude (largest first)
                amounts = []
                for amount in money_matches:
                    try:
                        amounts.append(float(str(amount).replace(',', '')))
                    except (ValueError, TypeError):
                        continue

                if amounts:
                    metrics["monetary_amounts"] = sorted(amounts, reverse=True)

                    # Try to identify specific amounts
                    if len(amounts) >= 1:
                        metrics["primary_amount"] = amounts[0]  # Usually the main result
                    if len(amounts) >= 2:
                        metrics["secondary_amount"] = amounts[1]  # Usually interest or savings

            # Extract percentages
            percent_pattern = r'([0-9,]+\.?\d*)%'
            percent_matches = re.findall(percent_pattern, response)
            if percent_matches and isinstance(percent_matches, list):
                percentages = []
                for pct in percent_matches:
                    try:
                        percentages.append(float(str(pct).replace(',', '')))
                    except (ValueError, TypeError):
                        continue

                if percentages:
                    metrics["percentages"] = percentages
                    metrics["primary_percentage"] = percentages[0]

            # Extract time periods (months, years)
            months_pattern = r'(\d+)\s*(?:month|months|mo)'
            months_matches = re.findall(months_pattern, response, re.IGNORECASE)
            if months_matches and isinstance(months_matches, list):
                try:
                    months_values = [int(m) for m in months_matches if str(m).isdigit()]
                    if months_values:
                        metrics["months"] = months_values
                        metrics["primary_months"] = months_values[0]
                except (ValueError, TypeError, IndexError):
                    pass

            # Extract dates (YYYY-MM-DD or Month YYYY)
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                r'([A-Za-z]+ \d{4})',     # Month YYYY
            ]
            for pattern in date_patterns:
                date_matches = re.findall(pattern, response)
                if date_matches and isinstance(date_matches, list):
                    metrics["dates"] = date_matches
                    break

        except Exception as e:
            print(f"⚠️ Error extracting metrics from response: {str(e)}")
            # Return empty metrics on error
            pass

        return metrics

    def _get_expected_metrics(self, expected: Dict[str, Any]) -> Dict[str, Any]:
        """Extract expected metrics from tool result."""

        metrics = {}

        # Extract key expected values based on scenario
        if expected.get("monthly_payment"):
            metrics["monthly_payment"] = expected["monthly_payment"]
        if expected.get("total_interest"):
            metrics["total_interest"] = expected["total_interest"]
        if expected.get("total_cost"):
            metrics["total_cost"] = expected["total_cost"]
        if expected.get("required_monthly_payment"):
            metrics["required_payment"] = expected["required_monthly_payment"]
        if expected.get("interest_saved"):
            metrics["interest_saved"] = expected["interest_saved"]
        if expected.get("months_saved"):
            metrics["months_saved"] = expected["months_saved"]
        if expected.get("total_payoff_months"):
            metrics["total_payoff_months"] = expected["total_payoff_months"]

        return metrics

    def _score_numerical_accuracy(self, expected: Dict[str, Any], extracted: Dict[str, Any]) -> float:
        """Score numerical accuracy (0-1 scale)."""

        tolerance = self.accuracy_config["tolerance_percent"]
        expected_metrics = self._get_expected_metrics(expected)


        if not expected_metrics:
            return 0.0  # No expected metrics to compare

        matches = 0
        total_checks = 0

        # Check each expected metric
        for key, expected_value in expected_metrics.items():
            if key in extracted and extracted[key] is not None:
                actual_value = extracted[key]
                total_checks += 1

                # Calculate percentage difference
                if expected_value != 0:
                    diff_percent = abs(actual_value - expected_value) / abs(expected_value)
                    if diff_percent <= tolerance:
                        matches += 1
                elif actual_value == 0:
                    matches += 1  # Both zero = exact match
            else:
                total_checks += 1  # Penalize missing values

        return matches / total_checks if total_checks > 0 else 0.0

    def _score_calculation_correctness(self, response: str, scenario_type: str) -> float:
        """Score calculation correctness (0-1 scale)."""

        score = 0.0
        factors = 0

        # Check for proper formulas based on scenario
        if scenario_type in ["current", "extra_payment", "refinance", "consolidate"]:
            # Should contain amortization formula or payment calculation
            if "amortization" in response.lower() or "M = P" in response or "monthly payment" in response.lower():
                score += 0.5
            factors += 1

        if scenario_type in ["extra_payment", "avalanche", "snowball"]:
            # Should mention interest savings or payoff acceleration
            if "interest" in response.lower() and ("save" in response.lower() or "saving" in response.lower()):
                score += 0.5
            factors += 1

        if scenario_type == "target_payoff":
            # Should mention solving for payment or annuity formula
            if "solve" in response.lower() or "required" in response.lower() or "payment" in response.lower():
                score += 0.5
            factors += 1

        # Check for mathematical operations
        if "+" in response or "-" in response or "*" in response or "/" in response:
            score += 0.3
            factors += 1

        # Check for showing work
        if "step" in response.lower() or "=" in response:
            score += 0.2
            factors += 1

        return score / factors if factors > 0 else 0.0

    def _score_explanation_quality(self, response: str) -> float:
        """Score explanation quality (0-1 scale)."""

        score = 0.0

        # Length check
        word_count = len(response.split())
        if word_count >= self.explanation_config["min_words"]:
            score += 0.3

        # Step-by-step check
        if "step" in response.lower() or "first" in response.lower() or "then" in response.lower():
            score += 0.3

        # Clarity indicators
        clarity_indicators = ["calculate", "formula", "using", "therefore", "so", "thus"]
        clarity_count = sum(1 for indicator in clarity_indicators if indicator in response.lower())
        score += min(0.4, clarity_count * 0.1)  # Max 0.4 for clarity

        return score

    def _get_numerical_scoring_details(self, expected: Dict[str, Any], extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed numerical scoring breakdown."""

        expected_metrics = self._get_expected_metrics(expected)
        details = {}

        for key, expected_value in expected_metrics.items():
            if key in extracted and extracted[key] is not None:
                actual_value = extracted[key]
                diff = abs(actual_value - expected_value)
                diff_percent = (diff / abs(expected_value) * 100) if expected_value != 0 else 0

                tolerance = self.accuracy_config["tolerance_percent"] * 100
                within_tolerance = diff_percent <= tolerance

                details[key] = {
                    "expected": expected_value,
                    "actual": actual_value,
                    "difference": round(diff, 2),
                    "difference_percent": round(diff_percent, 2),
                    "within_tolerance": within_tolerance,
                    "tolerance_limit": tolerance
                }
            else:
                details[key] = {
                    "expected": expected_value,
                    "actual": None,
                    "missing": True
                }

        return details

    def _get_calculation_scoring_details(self, response: str, scenario_type: str) -> Dict[str, Any]:
        """Get detailed calculation scoring breakdown."""

        return {
            "scenario_type": scenario_type,
            "has_amortization_formula": "amortization" in response.lower() or "M = P" in response,
            "has_mathematical_operations": any(op in response for op in ["+", "-", "*", "/"]),
            "shows_step_by_step": "step" in response.lower(),
            "mentions_key_concepts": self._check_key_concepts(response, scenario_type)
        }

    def _get_explanation_scoring_details(self, response: str) -> Dict[str, Any]:
        """Get detailed explanation scoring breakdown."""

        word_count = len(response.split())

        return {
            "word_count": word_count,
            "meets_minimum_length": word_count >= self.explanation_config["min_words"],
            "has_step_by_step": "step" in response.lower(),
            "clarity_indicators": sum(1 for word in ["calculate", "formula", "using", "therefore"]
                                    if word in response.lower())
        }

    def _check_key_concepts(self, response: str, scenario_type: str) -> List[str]:
        """Check for key financial concepts in response."""

        concepts = []

        # Common concepts
        if "principal" in response.lower():
            concepts.append("principal")
        if "interest" in response.lower():
            concepts.append("interest")
        if "payment" in response.lower():
            concepts.append("payment")

        # Scenario-specific concepts
        if scenario_type == "avalanche" and "highest" in response.lower():
            concepts.append("highest_rate_first")
        if scenario_type == "snowball" and "smallest" in response.lower():
            concepts.append("smallest_balance_first")
        if scenario_type == "refinance" and "lower" in response.lower():
            concepts.append("rate_reduction")
        if scenario_type == "consolidate" and ("combine" in response.lower() or "consolidate" in response.lower()):
            concepts.append("debt_consolidation")

        return concepts
