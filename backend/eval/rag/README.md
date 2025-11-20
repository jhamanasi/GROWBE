# Growbe Evaluation Harness

A comprehensive evaluation system for measuring the performance of RAG (Retrieval-Augmented Generation) vs baseline LLM responses for the Growbe financial advisor chatbot.

## 🎯 Overview

This evaluation harness compares two approaches:
- **Baseline**: LLM responses using only general knowledge
- **RAG**: LLM responses augmented with relevant context from a financial knowledge base

The system evaluates responses across multiple metrics:
- **Semantic Similarity**: How closely responses match expected answers
- **Keyword Overlap**: Common terminology usage
- **Hallucination Detection**: Avoidance of fabricated information

## 📊 Scoring Metrics

### Weighted Scoring System
- **Similarity**: 40% (semantic closeness to expected answer)
- **Keyword Match**: 40% (terminology overlap)
- **Hallucination Penalty**: 20% (penalty for made-up information)

### Score Ranges
- **0.0 - 1.0**: Higher scores indicate better performance
- **Threshold**: 0.7+ considered "passing"
- **Improvement**: Percentage improvement of RAG over baseline

## 🚀 Quick Start

### Prerequisites
```bash
# Install required packages
pip install sentence-transformers openai lancedb

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

### Run Full Evaluation
```bash
cd backend/eval
python eval_runner.py
```

### Quick Test (First 5 Questions)
```bash
python eval_runner.py --quick-test
```

### Custom Number of Questions
```bash
python eval_runner.py --max-questions 25
```

## 📁 Project Structure

```
backend/eval/
├── config.py                 # Configuration settings
├── eval_runner.py           # Main orchestration script
├── README.md               # This file
├── runners/
│   ├── rag_runner.py       # RAG evaluation runner
│   └── baseline_llm.py     # Baseline LLM runner
├── scorer/
│   ├── similarity_scorer.py    # Semantic similarity scorer
│   ├── keyword_scorer.py       # Keyword overlap scorer
│   └── hallucination_scorer.py # Hallucination detector
├── utils/
│   └── file_ops.py         # File I/O utilities
├── question_bank/
│   └── expected_answers.jsonl  # Expected answers for scoring
└── results/                # Generated evaluation results
```

## 📋 Question Bank

The evaluation uses 100 questions across financial categories:

- **Debt Management** (15 questions)
- **Credit Health** (10 questions)
- **Investment Basics** (10 questions)
- **Retirement Planning** (10 questions)
- **Insurance** (10 questions)
- **Tax Planning** (10 questions)
- **Estate Planning** (10 questions)
- **Mortgage Basics** (10 questions)
- **Student Loans** (10 questions)
- **Emergency Planning** (5 questions)

Each question has:
- Difficulty level: easy/medium/hard
- Expected answer for scoring
- Category classification

## 📊 Output Files

After evaluation, three files are generated in `results/`:

### 1. Detailed Results (`eval_results_YYYYMMDD-HHMMSS.jsonl`)
```json
{
  "question_id": 1,
  "question_text": "What is the difference between debt snowball and avalanche?",
  "category": "debt_management",
  "expected_answer": "Snowball pays smallest debts first...",
  "baseline_response": "The snowball method...",
  "rag_response": "Debt snowball focuses on...",
  "baseline_overall_score": 0.723,
  "rag_overall_score": 0.891,
  "improvement": 0.168,
  "improvement_percentage": 23.2
}
```

### 2. Summary CSV (`eval_summary_YYYYMMDD-HHMMSS.csv`)
Spreadsheet-friendly format with key metrics for analysis.

### 3. Report JSON (`eval_report_YYYYMMDD-HHMMSS.json`)
```json
{
  "total_questions": 100,
  "baseline_accuracy": 0.72,
  "rag_accuracy": 0.89,
  "improvement": 23.6,
  "by_category": {
    "debt_management": {"baseline": 0.71, "rag": 0.88, "improvement": 23.9},
    "credit_health": {"baseline": 0.73, "rag": 0.91, "improvement": 24.7}
  }
}
```

## 📈 Interpreting Results

### Overall Performance
```
Baseline Average Score: 0.721
RAG Average Score: 0.892
Improvement: +24.1%
```

### Category Analysis
- **Highest Improvement**: Categories where RAG helps most
- **Lowest Improvement**: Areas needing knowledge base expansion
- **Consistent Performance**: Categories with stable improvements

### Individual Question Analysis
- **RAG Failures**: Questions where context didn't help
- **Baseline Wins**: Questions where general LLM knowledge was sufficient
- **Hallucination Cases**: Responses with fabricated information

## 🔧 Configuration

### Model Settings (`config.py`)
```python
OPENAI_CONFIG = {
    "model": "gpt-4o-mini",
    "max_tokens": 2500,
    "temperature": 0.2,
}
```

### Scoring Weights
```python
SCORING_WEIGHTS = {
    "similarity": 0.4,
    "keyword": 0.4,
    "hallucination": 0.2,
}
```

### RAG Parameters
```python
RAG_CONFIG = {
    "top_k_chunks": 3,
    "knowledge_base": "financial_advice",
    "max_context_length": 2000,
}
```

## 🧪 Testing Individual Components

### Test RAG Runner
```bash
cd backend/eval/runners
python rag_runner.py
```

### Test Baseline Runner
```bash
python baseline_llm.py
```

### Test Scorers
```bash
cd backend/eval/scorer
python similarity_scorer.py
python keyword_scorer.py
python hallucination_scorer.py
```

## 📊 Visualization & Analysis

### Generate Charts (Future Enhancement)
```bash
# Planned: Automatic chart generation
python -m eval.visualize_results
```

### Manual Analysis with Pandas
```python
import pandas as pd
df = pd.read_csv('results/eval_summary_20241201-143000.csv')

# Category performance
df.groupby('category')[['baseline_overall_score', 'rag_overall_score']].mean()

# Improvement distribution
df['improvement_percentage'].hist()
```

## 🔍 Troubleshooting

### Common Issues

**1. OpenAI API Errors**
```bash
# Check API key
echo $OPENAI_API_KEY

# Verify key format
python -c "import openai; print('Key valid')"
```

**2. Knowledge Base Not Found**
```bash
# Check if vector database exists
ls -la backend/rag/vector_db/

# Re-ingest knowledge base if needed
cd backend/rag/scripts
python ingest_kbase.py
```

**3. Missing Dependencies**
```bash
pip install sentence-transformers openai lancedb
```

**4. Memory Issues**
```bash
# Reduce batch size in config
EVAL_CONFIG = {
    "batch_size": 5,  # Reduce from 10
}
```

### Performance Optimization

**For Large Evaluations:**
- Reduce `max_questions` parameter
- Use smaller models in config
- Increase `batch_size` for fewer API calls
- Run during off-peak hours

**For Detailed Analysis:**
- Set `save_intermediates: True` in config
- Review individual response details
- Analyze hallucination patterns

## 🤝 Contributing

### Adding New Questions
1. Add to `growbe_evaluation_question_bank.jsonl`
2. Add expected answer to `question_bank/expected_answers.jsonl`
3. Update category counts in this README

### Adding New Scorers
1. Create scorer in `scorer/` directory
2. Implement `score_response()` and `score_batch()` methods
3. Update weights in `config.py`
4. Integrate in `eval_runner.py`

### Custom Knowledge Bases
1. Add new KBase to `backend/rag/knowledge_bases/`
2. Run ingestion script
3. Update `knowledge_base` in RAG config

## 📈 Future Enhancements

- [ ] **Automated Chart Generation**: Matplotlib/Seaborn visualizations
- [ ] **Web Dashboard**: Interactive results exploration
- [ ] **Human-in-the-Loop Review**: Manual scoring interface
- [ ] **A/B Testing Framework**: Compare different RAG configurations
- [ ] **Performance Benchmarking**: Track improvements over time
- [ ] **Multi-Model Support**: Compare different LLM providers

## 📞 Support

For issues or questions:
1. Check this README
2. Review error logs in terminal output
3. Verify configuration in `config.py`
4. Test individual components

---

**Happy Evaluating! 🎯**
