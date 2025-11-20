"""
Main Evaluation Runner for Growbe Evaluation Harness

Orchestrates the complete evaluation pipeline:
1. Load questions and expected answers
2. Run RAG and baseline evaluations
3. Score responses using multiple metrics
4. Save results and generate reports
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables FIRST before any imports that might use them
backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=backend_dir / '.env')

# Add backend to path for imports
sys.path.insert(0, str(backend_dir))

from eval.rag.config import config
from eval.shared.utils.file_ops import (
    load_questions_from_jsonl,
    load_expected_answers,
    save_jsonl,
    save_csv,
    save_json,
    generate_timestamped_filename,
    create_evaluation_summary
)

from eval.runners.rag_runner import RAGRunner
from eval.runners.baseline_llm import BaselineLLMRunner

from eval.scorer.similarity_scorer import SimilarityScorer
from eval.scorer.keyword_scorer import KeywordScorer
from eval.scorer.hallucination_scorer import HallucinationScorer


class EvaluationRunner:
    """Main orchestrator for the evaluation pipeline."""

    def __init__(self):
        """Initialize the evaluation runner."""
        self.config = config
        self.questions = []
        self.expected_answers = {}
        self.results = []

        # Initialize components
        self.rag_runner = None
        self.baseline_runner = None
        self.similarity_scorer = None
        self.keyword_scorer = None
        self.hallucination_scorer = None

        print("✅ Evaluation Runner initialized")

    def load_data(self) -> bool:
        """
        Load questions and expected answers.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Load questions
            self.questions = load_questions_from_jsonl(self.config["paths"]["question_bank_file"])
            if not self.questions:
                print("❌ No questions loaded")
                return False

            # Load expected answers
            self.expected_answers = load_expected_answers(self.config["paths"]["expected_answers_file"])
            if not self.expected_answers:
                print("❌ No expected answers loaded")
                return False

            # Filter to questions that have expected answers
            question_ids_with_answers = set(self.expected_answers.keys())
            self.questions = [q for q in self.questions if q["question_id"] in question_ids_with_answers]

            if len(self.questions) < len(question_ids_with_answers):
                missing_answers = question_ids_with_answers - {q["question_id"] for q in self.questions}
                print(f"⚠️ Warning: {len(missing_answers)} questions missing from question bank")

            print(f"✅ Loaded {len(self.questions)} questions with expected answers")
            return True

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def initialize_components(self) -> bool:
        """
        Initialize all evaluation components.

        Returns:
            True if all components initialized successfully
        """
        try:
            print("🚀 Initializing evaluation components...")

            # Initialize runners
            self.rag_runner = RAGRunner()
            self.baseline_runner = BaselineLLMRunner()

            # Initialize scorers
            self.similarity_scorer = SimilarityScorer()
            self.keyword_scorer = KeywordScorer()
            self.hallucination_scorer = HallucinationScorer()

            print("✅ All components initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            return False

    def extract_queries(self, questions: List[Dict[str, Any]]) -> List[str]:
        """
        Extract question texts for evaluation.

        Args:
            questions: List of question dictionaries

        Returns:
            List of question text strings
        """
        return [q["question_text"] for q in questions]

    def load_baseline_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Load baseline responses from a previous CSV evaluation.

        Args:
            csv_path: Path to the CSV file containing previous results

        Returns:
            List of baseline response dictionaries
        """
        import pandas as pd

        try:
            df = pd.read_csv(csv_path)

            baseline_results = []
            for _, row in df.iterrows():
                baseline_results.append({
                    "query": row["question_text"],
                    "response": row["baseline_response"] if pd.notna(row["baseline_response"]) else "",
                    "success": bool(row["baseline_success"]) if pd.notna(row["baseline_success"]) else False
                })

            print(f"✅ Loaded {len(baseline_results)} baseline responses from {csv_path}")
            return baseline_results

        except Exception as e:
            print(f"❌ Error loading baseline from CSV: {e}")
            return []

    def combine_results(self, baseline_results: List[Dict], rag_results: List[Dict]) -> List[Dict]:
        """
        Combine baseline and RAG results into evaluation records.

        Args:
            baseline_results: Results from baseline runner
            rag_results: Results from RAG runner

        Returns:
            Combined evaluation records
        """
        combined_results = []

        for i, question in enumerate(self.questions):
            question_id = question["question_id"]
            expected_answer = self.expected_answers.get(question_id, "")

            record = {
                "question_id": question_id,
                "question_text": question["question_text"],
                "category": question["category"],
                "difficulty": question["difficulty"],
                "expected_answer": expected_answer,
                "baseline_response": baseline_results[i].get("response", ""),
                "baseline_success": baseline_results[i].get("success", False),
                "rag_response": rag_results[i].get("response", ""),
                "rag_success": rag_results[i].get("success", False),
                "rag_context_used": rag_results[i].get("context_used", False),
                "rag_context_length": rag_results[i].get("context_length", 0),
            }

            combined_results.append(record)

        return combined_results

    def score_results(self, results: List[Dict]) -> List[Dict]:
        """
        Score all results using multiple scorers.

        Args:
            results: Combined evaluation results

        Returns:
            Results with scores added
        """
        print("🏆 Starting comprehensive scoring...")

        scored_results = []
        total = len(results)

        for i, result in enumerate(results, 1):
            print(f"📊 Scoring question {i}/{total}: {result['question_text'][:50]}...")

            # Extract responses and expected answer
            baseline_response = result.get("baseline_response", "")
            rag_response = result.get("rag_response", "")
            expected_answer = result.get("expected_answer", "")

            # Score baseline response
            baseline_similarity = self.similarity_scorer.score_response(baseline_response, expected_answer)
            baseline_keyword = self.keyword_scorer.score_response(baseline_response, expected_answer)
            baseline_hallucination = self.hallucination_scorer.score_response(baseline_response, expected_answer)

            # Score RAG response
            rag_similarity = self.similarity_scorer.score_response(rag_response, expected_answer)
            rag_keyword = self.keyword_scorer.score_response(rag_response, expected_answer)
            rag_hallucination = self.hallucination_scorer.score_response(rag_response, expected_answer)

            # Calculate weighted scores
            weights = self.config["scoring_weights"]

            baseline_overall = (
                baseline_similarity["similarity_score"] * weights["similarity"] +
                baseline_keyword["keyword_score"] * weights["keyword"] +
                (1 - baseline_hallucination["hallucination_score"]) * weights["hallucination"]  # Lower hallucination is better
            )

            rag_overall = (
                rag_similarity["similarity_score"] * weights["similarity"] +
                rag_keyword["keyword_score"] * weights["keyword"] +
                (1 - rag_hallucination["hallucination_score"]) * weights["hallucination"]
            )

            # Add scores to result
            scored_result = result.copy()
            scored_result.update({
                # Baseline scores
                "baseline_similarity_score": baseline_similarity["similarity_score"],
                "baseline_keyword_score": baseline_keyword["keyword_score"],
                "baseline_hallucination_score": baseline_hallucination["hallucination_score"],
                "baseline_overall_score": round(baseline_overall, 3),

                # RAG scores
                "rag_similarity_score": rag_similarity["similarity_score"],
                "rag_keyword_score": rag_keyword["keyword_score"],
                "rag_hallucination_score": rag_hallucination["hallucination_score"],
                "rag_overall_score": round(rag_overall, 3),

                # Improvement
                "improvement": round(rag_overall - baseline_overall, 3),
                "improvement_percentage": round(((rag_overall - baseline_overall) / baseline_overall * 100) if baseline_overall > 0 else 0, 1),
            })

            scored_results.append(scored_result)

        print("✅ Scoring complete")
        return scored_results

    def run_evaluation(self, max_questions: Optional[int] = None, reuse_baseline: bool = False) -> bool:
        """
        Run the complete evaluation pipeline.

        Args:
            max_questions: Maximum number of questions to evaluate (None for all)
            reuse_baseline: If True, reuse baseline responses from previous evaluation

        Returns:
            True if evaluation completed successfully
        """
        start_time = time.time()

        try:
            print("🎯 Starting Growbe Evaluation Pipeline")
            print("=" * 50)

            # Load data
            if not self.load_data():
                return False

            # Limit questions if specified
            if max_questions and max_questions < len(self.questions):
                self.questions = self.questions[:max_questions]
                print(f"📊 Evaluating first {max_questions} questions")

            # Initialize components
            if not self.initialize_components():
                return False

            # Extract queries
            queries = self.extract_queries(self.questions)
            print(f"📝 Running evaluation on {len(queries)} questions")

            # Run baseline evaluation or load from previous results
            if reuse_baseline:
                print("♻️ Reusing baseline responses from previous evaluation...")
                # Find the most recent CSV file
                csv_files = sorted(Path(self.config["paths"]["results_dir"]).glob("eval_summary_*.csv"))
                if not csv_files:
                    print("❌ No previous evaluation results found!")
                    return False

                latest_csv = csv_files[-1]  # Most recent
                print(f"📂 Loading baseline from: {latest_csv}")
                baseline_results = self.load_baseline_from_csv(str(latest_csv))

                # Ensure we have the right number of baseline results
                if len(baseline_results) < len(queries):
                    print(f"⚠️ Warning: Only {len(baseline_results)} baseline results found, but {len(queries)} questions loaded")
                    # Pad with empty results if needed
                    while len(baseline_results) < len(queries):
                        baseline_results.append({"query": "", "response": "", "success": False})
                elif len(baseline_results) > len(queries):
                    # Trim to match current questions
                    baseline_results = baseline_results[:len(queries)]
            else:
                print("\n🤖 Running baseline evaluation (LLM only)...")
                baseline_results = self.baseline_runner.run_batch(queries)

            # Run RAG evaluation
            print("\n🧠 Running RAG evaluation (LLM + Knowledge Base)...")
            rag_results = self.rag_runner.run_batch(queries)

            # Combine results
            print("\n🔗 Combining results...")
            combined_results = self.combine_results(baseline_results, rag_results)

            # Score results
            print("\n🏆 Scoring responses...")
            self.results = self.score_results(combined_results)

            # Save results
            print("\n💾 Saving results...")
            self.save_results()

            # Print summary
            self.print_summary()

            elapsed_time = time.time() - start_time
            print(f"✅ Evaluation completed in {elapsed_time:.1f} seconds")
            return True

        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            return False

    def save_results(self) -> None:
        """Save evaluation results to files."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # Save detailed JSONL results
        jsonl_filename = f"eval_results_{timestamp}.jsonl"
        jsonl_path = self.config["paths"]["results_dir"] / jsonl_filename
        save_jsonl(self.results, jsonl_path)

        # Save CSV summary
        csv_filename = f"eval_summary_{timestamp}.csv"
        csv_path = self.config["paths"]["results_dir"] / csv_filename
        save_csv(self.results, csv_path)

        # Save JSON summary
        summary = create_evaluation_summary(self.results)
        summary_filename = f"eval_report_{timestamp}.json"
        summary_path = self.config["paths"]["results_dir"] / summary_filename
        save_json(summary, summary_path)

        print(f"📁 Results saved to:")
        print(f"  • {jsonl_path}")
        print(f"  • {csv_path}")
        print(f"  • {summary_path}")

    def print_summary(self) -> None:
        """Print evaluation summary to console."""
        if not self.results:
            print("❌ No results to summarize")
            return

        print("\n" + "=" * 60)
        print("📊 EVALUATION SUMMARY")
        print("=" * 60)

        # Overall metrics
        baseline_scores = [r["baseline_overall_score"] for r in self.results if r.get("baseline_success")]
        rag_scores = [r["rag_overall_score"] for r in self.results if r.get("rag_success")]

        baseline_avg = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0
        rag_avg = sum(rag_scores) / len(rag_scores) if rag_scores else 0
        improvement = ((rag_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0

        print(f"Questions Evaluated: {len(self.results)}")
        print(f"Baseline Success Rate: {len(baseline_scores)}/{len(self.results)} ({len(baseline_scores)/len(self.results)*100:.1f}%)")
        print(f"RAG Success Rate: {len(rag_scores)}/{len(self.results)} ({len(rag_scores)/len(self.results)*100:.1f}%)")
        print(f"Baseline Average Score: {baseline_avg:.3f}")
        print(f"RAG Average Score: {rag_avg:.3f}")
        print(f"Improvement: {improvement:+.1f}%")

        # Category breakdown
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"baseline": [], "rag": []}

            if result.get("baseline_success"):
                categories[cat]["baseline"].append(result["baseline_overall_score"])
            if result.get("rag_success"):
                categories[cat]["rag"].append(result["rag_overall_score"])

        print(f"\n📈 By Category:")
        for cat, scores in categories.items():
            baseline_cat_avg = sum(scores["baseline"]) / len(scores["baseline"]) if scores["baseline"] else 0
            rag_cat_avg = sum(scores["rag"]) / len(scores["rag"]) if scores["rag"] else 0
            cat_improvement = ((rag_cat_avg - baseline_cat_avg) / baseline_cat_avg * 100) if baseline_cat_avg > 0 else 0

            print(f"  {cat}: {baseline_cat_avg:.3f} → {rag_cat_avg:.3f} ({cat_improvement:+.1f}%)")

        print("\n✅ Evaluation complete! Check the results directory for detailed reports.")


def main():
    """Main entry point for running evaluations."""
    import argparse

    parser = argparse.ArgumentParser(description="Growbe Evaluation Harness")
    parser.add_argument("--max-questions", type=int, default=None,
                       help="Maximum number of questions to evaluate")
    parser.add_argument("--quick-test", action="store_true",
                       help="Run quick test with first 5 questions")
    parser.add_argument("--reuse-baseline", action="store_true",
                       help="Reuse baseline responses from previous evaluation")

    args = parser.parse_args()

    # Initialize and run evaluation
    runner = EvaluationRunner()

    max_questions = 5 if args.quick_test else args.max_questions

    success = runner.run_evaluation(max_questions=max_questions, reuse_baseline=args.reuse_baseline)

    if success:
        print("\n🎉 Evaluation completed successfully!")
        return 0
    else:
        print("\n❌ Evaluation failed!")
        return 1


if __name__ == "__main__":
    exit(main())
