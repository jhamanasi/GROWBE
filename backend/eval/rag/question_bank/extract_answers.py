#!/usr/bin/env python3

import json

# Read question IDs
with open('question_ids.txt', 'r') as f:
    question_ids = set(int(line.strip()) for line in f if line.strip())

print(f"Found {len(question_ids)} question IDs to extract")

# Read expected answers and filter
with open('expected_answers.jsonl', 'r') as f:
    all_answers = [json.loads(line) for line in f]

# Filter answers that match our question IDs
curated_answers = [answer for answer in all_answers if answer['question_id'] in question_ids]

print(f"Extracted {len(curated_answers)} matching expected answers")

# Write curated answers
with open('curated_expected_answers.jsonl', 'w') as f:
    for answer in curated_answers:
        f.write(json.dumps(answer) + '\n')

print("✅ Created curated_expected_answers.jsonl")
