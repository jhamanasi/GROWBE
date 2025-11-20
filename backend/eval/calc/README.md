# Calculation Evaluation

Evaluates LLM performance on financial calculations by comparing against the `debt_optimizer_tool` ground truth.

## Overview

This evaluation demonstrates the dramatic gap between:
- **Tool Accuracy**: 100% mathematically correct calculations using specialized financial tools
- **LLM Accuracy**: Variable accuracy with potential calculation errors, formula mistakes, and hallucinations

**Expected Results**: LLM scores will likely be 20-50% vs Tool's 100%, proving the value of specialized financial tools!

## Structure

```
calc/
├── config.py              # Configuration settings
├── eval_runner.py         # Main evaluation runner
├── question_bank/         # Calculation questions and expected answers
│   ├── calculation_questions.jsonl          # 20 diverse questions
│   ├── calculation_expected_answers.jsonl   # Ground truth from tool
│   └── generate_expected_answers.py         # Script to regenerate answers
├── results/              # Evaluation results and reports
├── runners/              # LLM calculation runner
│   └── llm_calculator.py
└── scorer/               # Calculation accuracy scorer
    └── calculation_scorer.py
```

## Question Coverage

The 20 questions cover all `debt_optimizer_tool` scenarios:

### **Basic Calculations (Easy)**
- Student loan payments ($25K @ 5.2% for 10 years)
- Auto loan payments ($35K @ 6.8% for 5 years)
- Mortgage payments ($300K @ 7.0% for 30 years)
- Credit card minimum payments ($8K @ 22.5%)
- Personal loan payments ($15K @ 12.0% for 3 years)

### **Advanced Scenarios (Medium)**
- Extra payments with interest savings
- Target payoff calculations (pay off in X months)
- Refinancing scenarios with new rates/terms
- Credit card promotional rates

### **Complex Strategies (Hard)**
- Debt consolidation (3+ debts into one)
- Debt avalanche (highest interest first)
- Debt snowball (smallest balance first)
- Multi-debt payoff optimization

## Usage

### Run Full Evaluation
```bash
cd backend/eval/calc
python eval_runner.py
```

### Run with Limited Questions
```bash
cd backend/eval/calc
python eval_runner.py --max-questions 5
```

## Sample Output

```
🧮 Starting Calculation Evaluation
📚 Loading questions and expected answers...
✅ Loaded 20 calculation questions

🤖 Running LLM calculations for 20 questions...
✅ LLM calculations completed: 18 successful, 2 failed

📊 Scoring LLM responses...
✅ Scoring completed!
   Average Total Score: 32.4%
   Average Numerical Accuracy: 28.7%

📈 Generating evaluation reports...
💾 Results saved to results/ folder
```

## Results Analysis

### **Scoring Breakdown**
- **Numerical Accuracy** (60%): Exact match within 1% tolerance
- **Calculation Correctness** (30%): Proper formulas and methods
- **Explanation Quality** (10%): Clear step-by-step reasoning

### **Expected Performance Gap**
```
Tool Performance:     100% (by definition)
LLM Performance:       20-50% (typical range)
Demonstration Value:   50-80% gap proves tool superiority
```

### **Common LLM Issues**
- Formula errors (wrong amortization equation)
- Calculation mistakes (arithmetic errors)
- Unit confusion (months vs years)
- Rounding inconsistencies
- Missing intermediate steps

## Results Files

Saved to `results/` folder:
- `calc_results_[timestamp].jsonl`: Detailed per-question results
- `calc_summary_[timestamp].csv`: Summary statistics
- `calc_report_[timestamp].json`: Full evaluation report

## Demo Presentation

Use these results to show:
1. **LLM Strengths**: Good at explaining concepts (+15.5% in RAG eval)
2. **LLM Weaknesses**: Poor at precise calculations (20-50% accuracy)
3. **Tool Value**: 100% accuracy for financial math
4. **Business Case**: Specialized tools > general AI for finance

## Integration

This evaluation complements the RAG evaluation:
- **RAG Eval**: Shows LLMs excel at knowledge retrieval (+15.5% improvement)
- **Calc Eval**: Shows LLMs struggle with mathematical precision (50-80% gap)

Together they prove: **"LLMs + Specialized Tools = Complete Financial AI Solution"**
