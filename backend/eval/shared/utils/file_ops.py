"""
File Operations Utilities for Growbe Evaluation Harness

Provides functions for loading and saving JSONL files, managing evaluation data,
and handling file I/O operations.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import pandas as pd

def load_jsonl(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load data from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of dictionaries containing the JSONL data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If JSON parsing fails
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"⚠️ Warning: Failed to parse line {line_num} in {file_path}: {e}")
                    continue

    print(f"✅ Loaded {len(data)} records from {file_path}")
    return data

def save_jsonl(data: List[Dict[str, Any]], file_path: Union[str, Path], append: bool = False) -> None:
    """
    Save data to a JSONL file.

    Args:
        data: List of dictionaries to save
        file_path: Path where to save the file
        append: If True, append to existing file instead of overwriting
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    mode = 'a' if append else 'w'
    with open(file_path, mode, encoding='utf-8') as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')

    action = "Appended" if append else "Saved"
    print(f"✅ {action} {len(data)} records to {file_path}")

def save_csv(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    """
    Save data to a CSV file.

    Args:
        data: List of dictionaries to save
        file_path: Path where to save the file
    """
    if not data:
        print("⚠️ Warning: No data to save to CSV")
        return

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Get all unique keys from all records
    all_keys = set()
    for record in data:
        all_keys.update(record.keys())

    fieldnames = sorted(all_keys)

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Saved {len(data)} records to CSV: {file_path}")

def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save data to a JSON file.

    Args:
        data: Dictionary to save
        file_path: Path where to save the file
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved JSON data to {file_path}")

def generate_timestamped_filename(base_name: str, extension: str = "jsonl") -> str:
    """
    Generate a timestamped filename for results.

    Args:
        base_name: Base name for the file (e.g., "rag_eval")
        extension: File extension (default: "jsonl")

    Returns:
        Timestamped filename string
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"

def load_questions_from_jsonl(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load questions from the question bank JSONL file.

    Args:
        file_path: Path to the question bank file

    Returns:
        List of question dictionaries
    """
    questions = load_jsonl(file_path)

    # Validate question format
    required_fields = ['question_id', 'question_text', 'category', 'difficulty']
    for question in questions:
        missing_fields = [field for field in required_fields if field not in question]
        if missing_fields:
            print(f"⚠️ Warning: Question {question.get('question_id', 'unknown')} missing fields: {missing_fields}")

    print(f"✅ Loaded {len(questions)} questions from question bank")
    return questions

def load_expected_answers(file_path: Union[str, Path]) -> Dict[int, str]:
    """
    Load expected answers from JSONL file.

    Args:
        file_path: Path to the expected answers file

    Returns:
        Dictionary mapping question_id to expected answer text
    """
    answers = load_jsonl(file_path)
    answer_dict = {}

    for answer in answers:
        if 'question_id' not in answer or 'expected_answer' not in answer:
            print(f"⚠️ Warning: Invalid answer format: {answer}")
            continue
        answer_dict[answer['question_id']] = answer['expected_answer']

    print(f"✅ Loaded {len(answer_dict)} expected answers")
    return answer_dict

def create_evaluation_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a summary of evaluation results.

    Args:
        results: List of evaluation result dictionaries

    Returns:
        Summary dictionary with statistics
    """
    if not results:
        return {"error": "No results to summarize"}

    # Calculate overall metrics
    baseline_scores = [r.get('baseline_score', 0) for r in results if r.get('baseline_score') is not None]
    rag_scores = [r.get('rag_score', 0) for r in results if r.get('rag_score') is not None]

    summary = {
        "total_questions": len(results),
        "baseline_questions": len(baseline_scores),
        "rag_questions": len(rag_scores),
        "baseline_accuracy": round(sum(baseline_scores) / len(baseline_scores), 3) if baseline_scores else 0,
        "rag_accuracy": round(sum(rag_scores) / len(rag_scores), 3) if rag_scores else 0,
        "improvement": round(
            ((sum(rag_scores) / len(rag_scores)) - (sum(baseline_scores) / len(baseline_scores))) / (sum(baseline_scores) / len(baseline_scores)) * 100,
            1
        ) if baseline_scores and rag_scores else 0,
    }

    # Category breakdown
    categories = {}
    for result in results:
        category = result.get('category', 'unknown')
        if category not in categories:
            categories[category] = {'baseline': [], 'rag': []}

        if result.get('baseline_score') is not None:
            categories[category]['baseline'].append(result['baseline_score'])
        if result.get('rag_score') is not None:
            categories[category]['rag'].append(result['rag_score'])

    summary['by_category'] = {}
    for category, scores in categories.items():
        baseline_avg = sum(scores['baseline']) / len(scores['baseline']) if scores['baseline'] else 0
        rag_avg = sum(scores['rag']) / len(scores['rag']) if scores['rag'] else 0
        improvement = ((rag_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0

        summary['by_category'][category] = {
            'baseline': round(baseline_avg, 3),
            'rag': round(rag_avg, 3),
            'improvement': round(improvement, 1),
            'count': len(scores['baseline'])
        }

    return summary

def export_results_to_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert evaluation results to a pandas DataFrame for analysis.

    Args:
        results: List of evaluation result dictionaries

    Returns:
        pandas DataFrame with results
    """
    return pd.DataFrame(results)
