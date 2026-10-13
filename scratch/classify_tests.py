import glob
import re

test_files = sorted(glob.glob('backend/tests/test_*.py'))
with_client = []
without_client = []

for tf in test_files:
    with open(tf, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'client:' in content or '(client' in content:
        with_client.append(tf)
    else:
        without_client.append(tf)

print(f'Files using client fixture: {len(with_client)}')
print(f'Files NOT using client fixture: {len(without_client)}')
