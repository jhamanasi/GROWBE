#!/usr/bin/env python3

import os
from pathlib import Path

# Debug path resolution in eval_runner.py context
current_file = Path(__file__).resolve()
eval_dir = current_file.parent
backend_dir = eval_dir.parent

print(f"Current file: {current_file}")
print(f"Eval dir: {eval_dir}")
print(f"Backend dir: {backend_dir}")

# This is the same logic as in eval_runner.py
backend_dir_from_eval = Path(__file__).resolve().parent.parent
print(f"backend_dir from eval_runner logic: {backend_dir_from_eval}")

env_path = backend_dir_from_eval / '.env'
print(f"env_path: {env_path}")
print(f"env file exists: {env_path.exists()}")

if env_path.exists():
    print("✅ .env file is accessible from eval directory")
else:
    print("❌ .env file is NOT accessible from eval directory")
    print("This is the problem!")
