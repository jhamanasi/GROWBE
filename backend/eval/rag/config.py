"""
Configuration for Growbe Evaluation Harness

This file contains all configuration settings for the RAG evaluation system,
including model parameters, file paths, and scoring weights.
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
    "max_tokens": 2500,
    "temperature": 0.2,  # Same temperature as main app
}

# File Paths
QUESTION_BANK_FILE = QUESTION_BANK_DIR / "growbe_evaluation_question_bank_curated.jsonl"
EXPECTED_ANSWERS_FILE = QUESTION_BANK_DIR / "curated_expected_answers.jsonl"

# Scoring Weights (0-1, must sum to 1)
SCORING_WEIGHTS = {
    "similarity": 0.4,      # Semantic similarity score
    "keyword": 0.4,         # Keyword overlap score
    "hallucination": 0.2,   # Hallucination penalty
}

# Similarity Scoring Parameters
SIMILARITY_CONFIG = {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "threshold": 0.7,  # Minimum similarity for "correct"
}

# Keyword Scoring Parameters
KEYWORD_CONFIG = {
    "min_overlap": 0.5,  # Minimum keyword overlap ratio
    "case_sensitive": False,
}

# Hallucination Detection Parameters
HALLUCINATION_CONFIG = {
    "max_confidence_threshold": 0.8,  # Above this = likely hallucination
    "fact_checking_enabled": True,
}

# RAG Configuration
RAG_CONFIG = {
    "top_k_chunks": 3,  # Number of chunks to retrieve
    "knowledge_base": "financial_concepts",  # Default KB to use
    "max_context_length": 2000,  # Max chars for context
}

# Evaluation Parameters
EVAL_CONFIG = {
    "max_questions": None,  # None = all questions
    "batch_size": 10,       # Questions per batch
    "save_intermediates": True,  # Save individual responses
    "generate_plots": True,  # Create visualization plots
}

# Report Configuration
REPORT_CONFIG = {
    "output_formats": ["jsonl", "csv", "json"],
    "include_individual_scores": True,
    "include_category_breakdown": True,
    "include_difficulty_breakdown": True,
}

# Human Review Configuration
HUMAN_REVIEW_CONFIG = {
    "auto_pass_threshold": 0.85,  # Scores above this need no review
    "auto_fail_threshold": 0.3,   # Scores below this are failed
    "review_queue_file": RESULTS_DIR / "human_review_queue.csv",
}

def get_config() -> Dict[str, Any]:
    """Get the complete evaluation configuration."""
    return {
        "openai": OPENAI_CONFIG,
        "scoring_weights": SCORING_WEIGHTS,
        "similarity": SIMILARITY_CONFIG,
        "keyword": KEYWORD_CONFIG,
        "hallucination": HALLUCINATION_CONFIG,
        "rag": RAG_CONFIG,
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
