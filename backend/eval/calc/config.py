"""
Configuration for Calculation Evaluation Harness

This file contains all configuration settings for the calculation evaluation system,
including model parameters, file paths, and scoring weights for mathematical accuracy.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Base evaluation directory
EVAL_DIR = Path(__file__).parent

# Subdirectories
RESULTS_DIR = EVAL_DIR / "results"
QUESTION_BANK_DIR = EVAL_DIR / "question_bank"
RUNNERS_DIR = EVAL_DIR / "runners"
SCORER_DIR = EVAL_DIR / "scorer"
UTILS_DIR = EVAL_DIR.parent / "shared" / "utils"

# Create directories if they don't exist
for dir_path in [RESULTS_DIR, QUESTION_BANK_DIR]:
    dir_path.mkdir(exist_ok=True)

# Model Configuration
OPENAI_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "model": "gpt-4o",  # Same model as main app
    "max_tokens": 1500,      # Shorter for calculations
    "temperature": 0.0,      # Zero temperature for consistency
}

# File Paths
QUESTION_BANK_FILE = QUESTION_BANK_DIR / "calculation_questions.jsonl"
EXPECTED_ANSWERS_FILE = QUESTION_BANK_DIR / "calculation_expected_answers.jsonl"

# Scoring Weights for Calculation Evaluation (0-1, must sum to 1)
SCORING_WEIGHTS = {
    "numerical_accuracy": 0.6,    # Exact numerical match
    "calculation_correctness": 0.3,  # Formula/method correctness
    "explanation_quality": 0.1,   # Clear explanation of steps
}

# Numerical Accuracy Parameters
ACCURACY_CONFIG = {
    "tolerance_percent": 0.01,     # 1% tolerance for floating point comparisons
    "exact_match_bonus": 1.0,      # Full points for exact matches
    "rounding_precision": 2,       # Round to 2 decimal places
}

# Calculation Correctness Parameters
CALCULATION_CONFIG = {
    "formula_detection": True,     # Check if correct formulas are used
    "step_by_step_required": True, # Require step-by-step explanations
    "common_errors_penalty": 0.2,  # Penalty for common calculation mistakes
}

# Explanation Quality Parameters
EXPLANATION_CONFIG = {
    "min_words": 10,              # Minimum words in explanation
    "clarity_score_weight": 0.5,   # Weight for explanation clarity
    "completeness_weight": 0.5,    # Weight for explanation completeness
}

# Tool Integration Configuration
TOOL_CONFIG = {
    "debt_optimizer_path": "backend.tools.debt_optimizer_tool",
    "tool_class_name": "DebtOptimizerTool",
    "mock_customer_data": False,   # Use mock data for testing
}

# Evaluation Parameters
EVAL_CONFIG = {
    "max_questions": None,        # None = all questions
    "batch_size": 5,              # Smaller batch for calculations
    "save_intermediates": True,   # Save individual responses
    "generate_plots": True,       # Create visualization plots
    "run_ground_truth": True,     # Generate tool-based ground truth
}

# Report Configuration
REPORT_CONFIG = {
    "output_formats": ["jsonl", "csv", "json"],
    "include_individual_scores": True,
    "include_calculation_breakdown": True,
    "include_error_analysis": True,
}

# Human Review Configuration
HUMAN_REVIEW_CONFIG = {
    "auto_pass_threshold": 0.95,  # Scores above this need no review
    "auto_fail_threshold": 0.5,   # Scores below this are failed
    "review_queue_file": RESULTS_DIR / "human_review_queue.csv",
}

def get_config() -> Dict[str, Any]:
    """Get the complete calculation evaluation configuration."""
    return {
        "openai": OPENAI_CONFIG,
        "scoring_weights": SCORING_WEIGHTS,
        "accuracy": ACCURACY_CONFIG,
        "calculation": CALCULATION_CONFIG,
        "explanation": EXPLANATION_CONFIG,
        "tool": TOOL_CONFIG,
        "eval": EVAL_CONFIG,
        "report": REPORT_CONFIG,
        "human_review": HUMAN_REVIEW_CONFIG,
        "paths": {
            "eval_dir": EVAL_DIR,
            "results_dir": RESULTS_DIR,
            "question_bank_dir": QUESTION_BANK_DIR,
            "question_bank_file": QUESTION_BANK_FILE,
            "expected_answers_file": EXPECTED_ANSWERS_FILE,
        }
    }

# Export config instance
config = get_config()
