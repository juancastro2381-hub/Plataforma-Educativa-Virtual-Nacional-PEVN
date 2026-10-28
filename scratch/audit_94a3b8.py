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

# Inspect files using #94A3B8
pattern = re.compile(r'(?:style=\{\{[^}]*color:\s*[\'"]#94A3B8[\'"][^}]*\}\}|color:\s*[\'"]#94A3B8[\'"])', re.IGNORECASE)

findings = []
for root, dirs, files in os.walk('frontend/src'):
    for f in files:
        if f.endswith(('.tsx', '.ts')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                lines = fh.readlines()
            for i, line in enumerate(lines):
                if '#94A3B8' in line.upper() and ('color' in line.lower() or 'style' in line.lower()):
                    # look backward up to 15 lines to see background
                    context = ''.join(lines[max(0, i-10):i+2])
                    is_dark = any(dark_indicator in context for dark_indicator in ['#0F172A', '#1E293B', '#0F172a', 'bg-slate-900', 'bg-gray-900', 'bg-gray-800'])
                    findings.append((os.path.relpath(p, 'frontend/src'), i+1, line.strip(), is_dark))

print(f"Total #94A3B8 usages: {len(findings)}")
light_bg_usages = [f for f in findings if not f[3]]
print(f"Usages without obvious dark container in preceding 10 lines: {len(light_bg_usages)}")
for f in light_bg_usages[:20]:
    print(f"{f[0]}:{f[1]} -> {f[2]}")

