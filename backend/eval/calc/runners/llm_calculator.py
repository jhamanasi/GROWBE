#!/usr/bin/env python3
"""
LLM Calculation Runner for Financial Calculations

This runner sends calculation questions to LLM and collects responses
to demonstrate calculation accuracy gaps vs specialized tools.
"""

# Load environment variables IMMEDIATELY before ANY other imports
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=backend_dir / '.env')

# Add backend to path for imports
sys.path.insert(0, str(backend_dir))

# Now import everything else
import time
from typing import Dict, Any, List
from datetime import datetime
from openai import OpenAI
from eval.calc.config import config


class LLMCalculator:
    """Runner for LLM-based financial calculations."""

    def __init__(self):
        self.client = OpenAI(api_key=config["openai"]["api_key"])
        self.model = config["openai"]["model"]
        self.max_tokens = config["openai"]["max_tokens"]
        self.temperature = config["openai"]["temperature"]

    def run_batch(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run calculations for a batch of questions using LLM.

        Args:
            questions: List of question dictionaries

        Returns:
            List of results with LLM responses and metadata
        """
        results = []

        for question in questions:
            print(f"🤖 Calculating question {question['question_id']}...")

            result = self._calculate_single(question)
            results.append(result)

            # Rate limiting
            time.sleep(1)

        return results

    def _calculate_single(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate a single question using LLM."""

        base_prompt = self._build_calculation_prompt(question)

        try:
            response = self.client.responses.create(
                model=self.model,
                input=base_prompt,
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
                truncation="auto"
            )

            response_text = response.output_text.strip() if hasattr(response, 'output_text') else str(response)

            return {
                "question_id": question["question_id"],
                "question_text": question["question_text"],
                "scenario_type": question.get("tool_params", {}).get("scenario_type", "unknown"),
                "llm_response": response_text,
                "success": True,
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ LLM calculation failed for question {question['question_id']}: {str(e)}")

            return {
                "question_id": question["question_id"],
                "question_text": question["question_text"],
                "scenario_type": question.get("tool_params", {}).get("scenario_type", "unknown"),
                "llm_response": "",
                "success": False,
                "error": str(e),
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }

    def _build_calculation_prompt(self, question: Dict[str, Any]) -> str:
        """Build a detailed calculation prompt for the LLM."""

        question_text = question["question_text"]
        scenario_type = question.get("tool_params", {}).get("scenario_type", "general")

        # Base instructions for financial calculations
        base_instructions = """You are a financial calculation assistant. You must perform accurate mathematical calculations for financial questions.

CRITICAL REQUIREMENTS:
1. Show ALL your work step by step
2. Use proper financial formulas (amortization, compound interest, etc.)
3. Round monetary amounts to 2 decimal places
4. Round percentages to 2 decimal places
5. Show intermediate calculations clearly
6. Provide final answer in a clear format

For loan/mortgage calculations, use the standard amortization formula:
M = P * (r(1+r)^n) / ((1+r)^n - 1)
Where:
- M = monthly payment
- P = principal amount
- r = monthly interest rate (annual rate / 12 / 100)
- n = number of payments

For savings/interest calculations, use compound interest formulas appropriately.
"""

        # Scenario-specific instructions
        scenario_instructions = self._get_scenario_instructions(scenario_type)

        # Format the final prompt
        prompt = f"""{base_instructions}

{scenario_instructions}

QUESTION: {question_text}

INSTRUCTIONS:
- Perform the exact calculation requested
- Show every step of your mathematical work
- Use proper financial formulas and terminology
- Format your final answer clearly

YOUR RESPONSE SHOULD INCLUDE:
1. Step-by-step calculation process
2. All intermediate values and formulas used
3. Final answer with proper formatting

Now calculate:"""

        return prompt

    def _get_scenario_instructions(self, scenario_type: str) -> str:
        """Get scenario-specific calculation instructions."""

        instructions = {
            "current": """
CURRENT PAYMENT CALCULATIONS:
- Calculate standard monthly payment for the given loan terms
- Use amortization formula for fixed-term loans
- For credit cards, calculate minimum payment (typically 2-3% of balance)
- Show the formula and all variables clearly
""",

            "extra_payment": """
EXTRA PAYMENT CALCULATIONS:
- First calculate the standard monthly payment
- Then add the extra payment amount
- Calculate how this affects payoff timeline and total interest
- Show before/after comparisons
- Calculate months saved and interest saved
""",

            "target_payoff": """
TARGET PAYOFF CALCULATIONS:
- Calculate required monthly payment to pay off debt in specified timeframe
- Use present value of annuity formula to solve for payment amount
- Show how much extra payment is needed beyond minimum
- Calculate total interest paid over the payoff period
""",

            "refinance": """
REFINANCING CALCULATIONS:
- Calculate new monthly payment at the lower interest rate
- Keep same principal amount and term length
- Calculate monthly savings and total savings over loan life
- Show before/after payment comparison
""",

            "consolidate": """
DEBT CONSOLIDATION CALCULATIONS:
- Sum all debt balances to get total principal
- Calculate weighted average interest rate (optional)
- Calculate new consolidated monthly payment
- Show monthly savings from combining debts
- Calculate total interest savings over time
""",

            "avalanche": """
DEBT AVALANCHE CALCULATIONS:
- Sort debts by interest rate (highest first)
- Apply extra payments to highest-rate debt first
- Calculate payoff order and timeline
- Show total interest saved vs minimum payments only
- Calculate months saved to debt freedom
""",

            "snowball": """
DEBT SNOWBALL CALCULATIONS:
- Sort debts by balance (smallest first)
- Apply extra payments to smallest debt first
- Calculate payoff order and timeline
- Show psychological benefits and momentum building
- Calculate total interest paid (may be higher than avalanche)
"""
        }

        return instructions.get(scenario_type, """
GENERAL FINANCIAL CALCULATIONS:
- Use appropriate financial formulas for the calculation type
- Show all mathematical steps clearly
- Use standard financial terminology
- Provide accurate numerical results
""")
