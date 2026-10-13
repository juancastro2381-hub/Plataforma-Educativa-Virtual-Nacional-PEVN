import glob
import re

test_files = sorted(glob.glob('backend/tests/test_*.py'))
print(f'Total test files: {len(test_files)}')

total_test_funcs = 0
for tf in test_files:
    with open(tf, 'r', encoding='utf-8') as f:
        content = f.read()
    funcs = re.findall(r'def (test_\w+)', content)
    total_test_funcs += len(funcs)

print(f'Total test functions defined across files: {total_test_funcs}')
