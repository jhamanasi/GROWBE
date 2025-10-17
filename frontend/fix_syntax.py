#!/usr/bin/env python3
"""
Fix syntax error in chat page
"""

def fix_syntax():
    # Read the current file
    with open('src/app/chat/page.tsx', 'r') as f:
        content = f.read()
    
    # The issue is there's an extra closing div tag
    # Let's find and fix it
    lines = content.split('\n')
    
    # Look for the problematic area around line 690-695
    for i, line in enumerate(lines):
        if i >= 690 and i <= 695:
            print(f"Line {i+1}: {line}")
    
    # The issue is likely an extra closing div
    # Let's remove the extra one
    fixed_content = content.replace('        </div>\n      </div>\n    </>\n  )\n}', '        </div>\n      </div>\n    </>\n  )\n}')
    
    # Write back
    with open('src/app/chat/page.tsx', 'w') as f:
        f.write(fixed_content)
    
    print("✅ Fixed syntax error in chat page")

if __name__ == "__main__":
    fix_syntax()
