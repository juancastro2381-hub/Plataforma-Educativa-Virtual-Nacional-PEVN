import os
import re

def lum(r, g, b):
    a = []
    for c in [r, g, b]:
        v = c / 255.0
        a.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

def hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c*2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def cr(c1, c2):
    l1 = lum(*c1)
    l2 = lum(*c2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

white = (255, 255, 255)
slate_50 = hex2rgb('F8FAFC')

pattern = re.compile(r'color:\s*[\'"](#(?:[0-9a-fA-F]{3}){1,2})[\'"]')

results = {}
for root, dirs, files in os.walk('frontend/src'):
    for f in files:
        if f.endswith(('.tsx', '.ts')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                content = fh.read()
            for m in pattern.finditer(content):
                hex_val = m.group(1).upper()
                if len(hex_val) == 4:
                    hex_val = '#' + ''.join(c*2 for c in hex_val[1:])
                c_ratio_white = cr(hex2rgb(hex_val), white)
                rel = os.path.relpath(p, 'frontend/src')
                if c_ratio_white < 4.5:
                    results.setdefault(hex_val, []).append((rel, c_ratio_white))

print(f"Total low-contrast (< 4.5:1 on white) hex colors found: {len(results)}")
for hex_val, occurrences in sorted(results.items(), key=lambda x: -len(x[1])):
    print(f"{hex_val} (contrast on white: {occurrences[0][1]:.2f}): {len(occurrences)} occurrences across {len(set(o[0] for o in occurrences))} files")
    for f, ratio in sorted(set(occurrences))[:5]:
        print(f"   - {f}")

