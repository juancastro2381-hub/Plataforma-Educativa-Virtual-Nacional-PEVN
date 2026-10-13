with open(r'C:\Users\juanc\.gemini\antigravity-ide\brain\c8d91982-b185-46e3-b466-0e6946a78297\.system_generated\tasks\task-1168.log', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
failures = re.findall(r'FAILURES ===.*?(?=== short test summary info)', text, re.DOTALL)
if failures:
    for fail_section in failures:
        lines = fail_section.split('\n')
        # print first 50 lines of failures
        for l in lines[:100]:
            print(l)
else:
    print('No FAILURES section found')
