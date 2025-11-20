#!/usr/bin/env python3
"""
Generate expected answers for calculation questions using debt_optimizer_tool.
"""

import sys
import json
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
print(f"Backend dir: {backend_dir}")
sys.path.insert(0, str(backend_dir))

from eval.calc.tools.evaluation_debt_optimizer import EvaluationDebtOptimizer
from eval.shared.utils.file_ops import load_jsonl, save_jsonl

def generate_expected_answer(question):
    """Generate expected answer using evaluation debt optimizer."""

    tool_params = question.get("tool_params", {})

    # Initialize evaluation tool
    tool = EvaluationDebtOptimizer()

    try:
        # Call the evaluation tool with the question parameters
        result = tool.process_hypothetical_debts(**tool_params)

        if result.get("status") == "error":
            print(f"❌ Error for question {question['question_id']}: {result.get('error')}")
            return None

        # Extract key metrics based on scenario type
        scenario_type = tool_params.get("scenario_type", "current")

        expected_answer = {
            "question_id": question["question_id"],
            "scenario_type": scenario_type,
            "tool_result": result
        }

        # Extract specific metrics for easy comparison and format for evaluation
        if scenario_type == "current":
            # Single debt current payment
            if "debts" in result and len(result["debts"]) == 1:
                debt = result["debts"][0]
                expected_answer.update({
                    "monthly_payment": round(debt.get("new_payment", 0), 2),  # Use new_payment for current scenario
                    "total_cost": None,  # Not calculated for current scenario
                    "total_interest": None
                })

        elif scenario_type == "extra_payment":
            # Extra payment savings
            if "debts" in result and len(result["debts"]) == 1:
                debt = result["debts"][0]
                extra_details = debt.get("extra_payment_details", {})
                expected_answer.update({
                    "monthly_payment": round(debt.get("new_payment", 0), 2),
                    "total_interest": round(extra_details.get("total_interest", 0), 2),
                    "original_total_interest": round(extra_details.get("original_total_interest", 0), 2),
                    "interest_saved": round(extra_details.get("total_savings", 0), 2),
                    "months_saved": extra_details.get("months_saved", 0),
                    "payoff_date": extra_details.get("payoff_date")
                })

        elif scenario_type == "target_payoff":
            # Target payoff calculations
            if "debts" in result and len(result["debts"]) == 1:
                debt = result["debts"][0]
                expected_answer.update({
                    "required_monthly_payment": round(debt.get("required_payment", 0), 2),
                    "total_interest": round(debt.get("total_interest", 0), 2),
                    "total_cost": round(debt.get("total_cost", 0), 2),
                    "payoff_months": debt.get("target_payoff_months", 0),
                    "payoff_date": debt.get("target_payoff_date")
                })

        elif scenario_type in ["refinance", "consolidate"]:
            # Refinancing/consolidation
            expected_answer.update({
                "monthly_payment": round(result.get("summary", {}).get("total_new_payment", 0), 2),
                "total_savings": round(result.get("summary", {}).get("total_savings", 0), 2),
                "monthly_savings": round(result.get("summary", {}).get("monthly_savings", 0), 2),
                "break_even_months": result.get("summary", {}).get("break_even_analysis", {}).get("break_even_months")
            })

        elif scenario_type in ["avalanche", "snowball"]:
            # Multi-debt payoff strategies
            expected_answer.update({
                "total_interest_paid": round(result.get("total_interest_paid", 0), 2),
                "total_interest_saved": round(result.get("total_interest_saved", 0), 2),
                "total_months_saved": result.get("total_months_saved", 0),
                "total_payoff_months": result.get("total_payoff_months", 0),
                "payoff_timeline": result.get("payoff_timeline", [])
            })

        # Create expected_answer field for evaluation framework
        if scenario_type == "current":
            expected_answer["expected_answer"] = f"${expected_answer['monthly_payment']:.2f}"
        elif scenario_type == "extra_payment":
            expected_answer["expected_answer"] = f"${expected_answer['monthly_payment']:.2f} monthly payment, ${expected_answer['interest_saved']:.2f} interest saved, {expected_answer['months_saved']} months saved"
        elif scenario_type == "target_payoff":
            expected_answer["expected_answer"] = f"${expected_answer['required_monthly_payment']:.2f} monthly payment, ${expected_answer['total_interest']:.2f} total interest, payoff in {expected_answer['payoff_months']} months"
        elif scenario_type == "refinance":
            expected_answer["expected_answer"] = f"${expected_answer['monthly_savings']:.2f} monthly savings, ${expected_answer['total_savings']:.2f} total savings"
        elif scenario_type == "consolidate":
            expected_answer["expected_answer"] = f"${expected_answer['monthly_savings']:.2f} monthly savings, ${expected_answer['total_savings']:.2f} total savings"
        elif scenario_type in ["avalanche", "snowball"]:
            expected_answer["expected_answer"] = f"${expected_answer['total_interest_paid']:.2f} total interest paid, payoff in {expected_answer['total_payoff_months']} months"
        else:
            expected_answer["expected_answer"] = "Calculation completed successfully"

        return expected_answer

    except Exception as e:
        print(f"❌ Exception for question {question['question_id']}: {str(e)}")
        return None

def main():
    """Generate expected answers for all calculation questions."""

    print("🧮 Generating expected answers using evaluation debt optimizer...")

    # Load questions
    questions_file = Path(__file__).parent / "calculation_questions.jsonl"
    questions = load_jsonl(questions_file)

    print(f"📚 Loaded {len(questions)} questions")

    expected_answers = []

    for i, question in enumerate(questions, 1):
        print(f"🔢 Processing question {i}/{len(questions)}: ID {question['question_id']}")

        expected_answer = generate_expected_answer(question)
        if expected_answer:
            expected_answers.append(expected_answer)
            print(f"   ✅ Generated answer")
        else:
            print(f"   ❌ Failed to generate answer")

    # Save expected answers
    answers_file = Path(__file__).parent / "calculation_expected_answers.jsonl"
    save_jsonl(expected_answers, answers_file)

    print(f"💾 Saved {len(expected_answers)} expected answers to {answers_file}")

    # Also save as formatted JSON for easier inspection
    json_file = Path(__file__).parent / "calculation_expected_answers.json"
    with open(json_file, 'w') as f:
        json.dump(expected_answers, f, indent=2, default=str)

    print(f"📋 Also saved formatted JSON to {json_file}")

if __name__ == "__main__":
    main()
