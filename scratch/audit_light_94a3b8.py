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

# Inspect files for #94A3B8, #A0AEC0, #CBD5E1 on light containers
light_issues = []

for root, dirs, files in os.walk('frontend/src'):
    for f in files:
        if f.endswith(('.tsx', '.ts')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                lines = fh.readlines()
            # Track if inside a dark container
            # Simple heuristic: scan line by line
            dark_depth = 0
            for i, line in enumerate(lines):
                # check if line has #94A3B8 in a color context
                if '#94A3B8' in line.upper() and ('color' in line.lower() or 'style' in line.lower()):
                    # look back 20 lines for nearest background-color or bg-
                    bg = 'light' # default page is light
                    for prev_line in lines[max(0, i-25):i+1]:
                        if any(dark_bg in prev_line for dark_bg in ['#0F172A', '#1E293B', '#020617', 'bg-slate-900', 'bg-gray-900', 'bg-gray-800', '#111827', '#0F172a']):
                            bg = 'dark'
                        if any(light_bg in prev_line for light_bg in ['#FFFFFF', '#F8FAFC', 'bg-white', 'backgroundColor: \'#FFFFFF\'', 'backgroundColor: \'#F8FAFC\'']):
                            bg = 'light'
                    if bg == 'light':
                        light_issues.append((os.path.relpath(p, 'frontend/src'), i+1, line.strip()))

print(f"Total suspected light-bg #94A3B8 issues: {len(light_issues)}")
for f in light_issues:
    print(f"{f[0]}:{f[1]} -> {f[2]}")

