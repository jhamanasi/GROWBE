#!/usr/bin/env python3
"""
Calculation Evaluation Runner

Evaluates LLM performance on financial calculations by comparing against
the debt_optimizer_tool ground truth.
"""

# Load environment variables IMMEDIATELY before ANY other imports
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=backend_dir / '.env')

# Add backend to path for imports
sys.path.insert(0, str(backend_dir))

# Now import everything else
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from eval.calc.config import config
from eval.calc.runners.llm_calculator import LLMCalculator
from eval.calc.scorer.calculation_scorer import CalculationScorer
from eval.shared.utils.file_ops import (
    load_jsonl,
    load_questions_from_jsonl,
    load_expected_answers,
    save_jsonl,
    save_csv,
    save_json,
    generate_timestamped_filename,
    create_evaluation_summary
)


class CalculationEvaluationRunner:
    """Runner for calculation evaluation comparing LLM vs Tool performance."""

    def __init__(self):
        self.config = config
        self.questions = []
        self.expected_answers = []
        self.llm_calculator = LLMCalculator()
        self.scorer = CalculationScorer()

    def run_evaluation(self, max_questions: Optional[int] = None) -> bool:
        """
        Run the complete calculation evaluation pipeline.

        Args:
            max_questions: Maximum number of questions to evaluate (None = all)

        Returns:
            bool: Success status
        """
        print("🧮 Starting Calculation Evaluation")
        print("=" * 50)

        try:
            # Load questions and expected answers
            print("📚 Loading questions and expected answers...")
            self.questions = load_questions_from_jsonl(self.config['paths']['question_bank_file'])
            # Load full expected answer objects (not just the answer strings)
            expected_answers_full = load_jsonl(self.config['paths']['expected_answers_file'])
            self.expected_answers = expected_answers_full
            # Also create the expected answers dict for compatibility
            self.expected_answers_dict = load_expected_answers(self.config['paths']['expected_answers_file'])

            if max_questions:
                self.questions = self.questions[:max_questions]
                self.expected_answers = self.expected_answers[:max_questions]

            print(f"✅ Loaded {len(self.questions)} calculation questions")

            # Generate ground truth if needed
            if self.config['eval']['run_ground_truth']:
                print("\n🔧 Generating ground truth using debt_optimizer_tool...")
                ground_truth_results = self._generate_ground_truth()
            else:
                print("\n⏭️  Skipping ground truth generation")
                ground_truth_results = []

            # Check for existing LLM results backup
            import json
            from pathlib import Path

            llm_results_file = self.config['paths']['results_dir'] / "llm_results_backup.json"

            if llm_results_file.exists():
                print(f"\n📂 Found existing LLM results backup at {llm_results_file}")
                print("💰 Loading from backup to save costs...")

                with open(llm_results_file, 'r') as f:
                    llm_results = json.load(f)

                successful_results = [r for r in llm_results if r["success"]]
                failed_results = [r for r in llm_results if not r["success"]]

                print(f"✅ Loaded {len(successful_results)} successful, {len(failed_results)} failed LLM results from backup")
            else:
                # Run LLM calculations
                print("\n🤖 Running LLM calculations...")
                llm_results = self._run_llm_calculations()

                # Save LLM results before scoring (in case scoring fails)
                with open(llm_results_file, 'w') as f:
                    json.dump(llm_results, f, indent=2)
                print(f"💾 LLM results saved to {llm_results_file}")

            # Score and compare
            print("\n📊 Scoring and comparing results...")
            print(f"   About to call _score_and_compare with {len(ground_truth_results)} ground truth and {len(llm_results)} LLM results")
            try:
                evaluation_results = self._score_and_compare(ground_truth_results, llm_results)
                print("   _score_and_compare completed successfully")
            except Exception as e:
                print(f"   _score_and_compare failed: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

            # Generate reports
            print("\n📈 Generating evaluation reports...")
            self._generate_reports(evaluation_results)

            print("\n✅ Calculation evaluation completed!")
            return True

        except Exception as e:
            print(f"\n❌ Evaluation failed: {str(e)}")
            return False

    def _generate_ground_truth(self) -> List[Dict[str, Any]]:
        """Generate ground truth using the debt_optimizer_tool."""
        # Ground truth is already generated and saved as expected_answers.jsonl
        # We just need to load it
        print("✅ Ground truth already available in expected_answers.jsonl")
        return self.expected_answers

    def _run_llm_calculations(self) -> List[Dict[str, Any]]:
        """Run calculations using LLM."""
        print(f"🤖 Running LLM calculations for {len(self.questions)} questions...")

        llm_results = self.llm_calculator.run_batch(self.questions)

        # Filter successful results
        successful_results = [r for r in llm_results if r["success"]]
        failed_results = [r for r in llm_results if not r["success"]]

        print(f"✅ LLM calculations completed: {len(successful_results)} successful, {len(failed_results)} failed")

        if failed_results:
            print(f"❌ Failed questions: {[r['question_id'] for r in failed_results]}")

        return llm_results

    def _score_and_compare(self, ground_truth: List[Dict[str, Any]],
                          llm_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score and compare ground truth vs LLM results."""

        print("📊 Scoring LLM responses...")
        print(f"   Ground truth count: {len(ground_truth)}")
        print(f"   LLM results count: {len(llm_results)}")

        # Debug first items
        if ground_truth:
            print(f"   First ground truth keys: {list(ground_truth[0].keys())}")
        if llm_results:
            print(f"   First LLM result keys: {list(llm_results[0].keys())}")

        scored_results = []
        summary_stats = {
            "total_questions": len(self.questions),
            "successful_llm_responses": 0,
            "average_total_score": 0.0,
            "average_numerical_accuracy": 0.0,
            "average_calculation_correctness": 0.0,
            "average_explanation_quality": 0.0,
            "scenario_breakdown": {},
            "score_distribution": {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        }

        total_scores = []
        numerical_scores = []
        calculation_scores = []
        explanation_scores = []

        for llm_result in llm_results:
            question_id = llm_result["question_id"]

            # Find corresponding expected answer
            expected = next((e for e in ground_truth if e["question_id"] == question_id), None)
            if not expected:
                print(f"⚠️ No expected answer found for question {question_id}")
                continue

            # Score the response
            try:
                score_result = self.scorer.score_response(expected, llm_result)
                scored_results.append({
                    "question_id": question_id,
                    "question_text": llm_result["question_text"],
                    "expected_answer": expected,
                    "llm_response": llm_result,
                    "scoring": score_result
                })

                # Update summary stats
                if llm_result["success"]:
                    summary_stats["successful_llm_responses"] += 1

                    total_score = score_result["total_score"]
                    numerical_score = score_result["numerical_accuracy"]
                    calculation_score = score_result["calculation_correctness"]
                    explanation_score = score_result["explanation_quality"]

                    total_scores.append(total_score)
                    numerical_scores.append(numerical_score)
                    calculation_scores.append(calculation_score)
                    explanation_scores.append(explanation_score)

                    # Categorize performance
                    if total_score >= 0.9:
                        summary_stats["score_distribution"]["excellent"] += 1
                    elif total_score >= 0.7:
                        summary_stats["score_distribution"]["good"] += 1
                    elif total_score >= 0.5:
                        summary_stats["score_distribution"]["fair"] += 1
                    else:
                        summary_stats["score_distribution"]["poor"] += 1

                    # Scenario breakdown
                    scenario = score_result["scenario_type"]
                    if scenario not in summary_stats["scenario_breakdown"]:
                        summary_stats["scenario_breakdown"][scenario] = {"count": 0, "avg_score": 0.0}

                    summary_stats["scenario_breakdown"][scenario]["count"] += 1
                    summary_stats["scenario_breakdown"][scenario]["avg_score"] += total_score

            except Exception as e:
                print(f"❌ Scoring failed for question {question_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        # Calculate averages
        if total_scores:
            summary_stats["average_total_score"] = round(sum(total_scores) / len(total_scores), 3)
            summary_stats["average_numerical_accuracy"] = round(sum(numerical_scores) / len(numerical_scores), 3)
            summary_stats["average_calculation_correctness"] = round(sum(calculation_scores) / len(calculation_scores), 3)
            summary_stats["average_explanation_quality"] = round(sum(explanation_scores) / len(explanation_scores), 3)

        # Calculate scenario averages
        for scenario, data in summary_stats["scenario_breakdown"].items():
            if data["count"] > 0:
                data["avg_score"] = round(data["avg_score"] / data["count"], 3)

        print("✅ Scoring completed!")
        print(f"   Average Total Score: {summary_stats['average_total_score']:.1%}")
        print(f"   Average Numerical Accuracy: {summary_stats['average_numerical_accuracy']:.1%}")

        return {
            "summary": summary_stats,
            "detailed_results": scored_results
        }

    def _generate_reports(self, evaluation_results: Dict[str, Any]) -> None:
        """Generate evaluation reports."""
        timestamp = generate_timestamped_filename("calc_eval")

        # Save detailed results
        results_file = self.config['paths']['results_dir'] / f"calc_results_{timestamp}.jsonl"
        save_jsonl(evaluation_results.get('detailed_results', []), results_file)

        # Save summary as JSON (since it's a single object)
        summary_file = self.config['paths']['results_dir'] / f"calc_summary_{timestamp}.json"
        save_json(evaluation_results.get('summary', {}), summary_file)

        # Save full report
        report_file = self.config['paths']['results_dir'] / f"calc_report_{timestamp}.json"
        save_json(evaluation_results, report_file)

        print(f"📁 Results saved to: {self.config['paths']['results_dir']}")


def main():
    """Main entry point for calculation evaluation."""
    import argparse

    parser = argparse.ArgumentParser(description="Run calculation evaluation")
    parser.add_argument("--max-questions", type=int, default=None,
                       help="Maximum number of questions to evaluate")
    parser.add_argument("--skip-ground-truth", action="store_true",
                       help="Skip ground truth generation")

    args = parser.parse_args()

    # Update config if needed
    if args.skip_ground_truth:
        config['eval']['run_ground_truth'] = False

    # Run evaluation
    runner = CalculationEvaluationRunner()
    success = runner.run_evaluation(max_questions=args.max_questions)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
