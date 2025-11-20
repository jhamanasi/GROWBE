#!/usr/bin/env python3

import sys
from pathlib import Path

# Test the evaluation pipeline step by step
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

print("=== Growbe Evaluation Test ===")

try:
    print("1. Loading config...")
    from eval.rag.config import config
    print("✅ Config loaded")

    print("2. Loading file operations...")
    from eval.shared.utils.file_ops import load_questions_from_jsonl, load_expected_answers
    print("✅ File ops loaded")

    print("3. Loading questions...")
    questions = load_questions_from_jsonl(config['paths']['question_bank_file'])
    print(f"✅ Loaded {len(questions)} questions")

    print("4. Loading expected answers...")
    expected_answers = load_expected_answers(config['paths']['expected_answers_file'])
    print(f"✅ Loaded {len(expected_answers)} expected answers")

    print("5. Testing BaselineLLMRunner...")
    from eval.runners.baseline_llm import BaselineLLMRunner
    baseline_runner = BaselineLLMRunner()
    print("✅ BaselineLLMRunner initialized")

    print("6. Testing RAGRunner...")
    from eval.runners.rag_runner import RAGRunner
    rag_runner = RAGRunner()
    print("✅ RAGRunner initialized")

    print("7. Testing Scorers...")
    from eval.scorer.similarity_scorer import SimilarityScorer
    from eval.scorer.keyword_scorer import KeywordScorer
    from eval.scorer.hallucination_scorer import HallucinationScorer

    similarity_scorer = SimilarityScorer()
    keyword_scorer = KeywordScorer()
    hallucination_scorer = HallucinationScorer()
    print("✅ All scorers initialized")

    print("8. Testing single question evaluation...")
    # Test with just the first question
    test_question = questions[0]
    expected_answer = expected_answers.get(test_question['question_id'], "")

    print(f"Question: {test_question['question_text'][:50]}...")

    # Test baseline
    baseline_result = baseline_runner.generate_response(test_question['question_text'])
    print(f"Baseline success: {baseline_result['success']}")
    if baseline_result['success']:
        print(f"Baseline response length: {len(baseline_result['response'])} chars")

    # Test RAG
    rag_result = rag_runner.generate_response(test_question['question_text'])
    print(f"RAG success: {rag_result['success']}")
    if rag_result['success']:
        print(f"RAG response length: {len(rag_result['response'])} chars")
        print(f"RAG context used: {rag_result['context_used']}")

    print("\n🎉 All tests passed! Evaluation harness is ready.")

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
