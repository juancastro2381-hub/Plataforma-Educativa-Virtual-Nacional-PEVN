import os
import re

src_dir = r"frontend\src"

# Function to calculate relative luminance
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c * 2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def get_luminance(r, g, b):
    def channel_lum(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r_l = channel_lum(r)
    g_l = channel_lum(g)
    b_l = channel_lum(b)
    return 0.2126 * r_l + 0.7152 * g_l + 0.0722 * b_l

def contrast_ratio(l1, l2):
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

# Known color values in the codebase
known_colors = {
    '#ffffff': get_luminance(255, 255, 255),
    '#fcfbfa': get_luminance(252, 251, 250),
    '#f8fafc': get_luminance(248, 250, 252),
    '#f1f5f9': get_luminance(241, 245, 249),
    '#e2e8f0': get_luminance(226, 232, 240),
    '#cbd5e1': get_luminance(203, 213, 225),
    '#94a3b8': get_luminance(148, 163, 184),
    '#64748b': get_luminance(100, 116, 139),
    '#475569': get_luminance(71, 85, 105),
    '#334155': get_luminance(51, 65, 85),
    '#1e293b': get_luminance(30, 41, 59),
    '#0f172a': get_luminance(15, 23, 42),
    '#000000': get_luminance(0, 0, 0),
    '#1e3a8a': get_luminance(30, 58, 138),
    '#1e40af': get_luminance(30, 64, 175),
    '#010066': get_luminance(1, 0, 102),
    '#fcd116': get_luminance(252, 209, 22),
    '#fde047': get_luminance(253, 224, 71),
    '#fef08a': get_luminance(254, 240, 138),
    '#3b82f6': get_luminance(59, 130, 246),
    '#2563eb': get_luminance(37, 99, 235),
    '#1d4ed8': get_luminance(29, 78, 216),
}

# Scan all files for potential inline styles with background and color
inline_style_regex = re.compile(r"style=\{\{([^}]+)\}\}", re.DOTALL)

suspicious_findings = []

for root, dirs, files in os.walk(src_dir):
    for f in files:
        if f.endswith('.tsx'):
            p = os.path.join(root, f)
            rel_p = os.path.relpath(p, src_dir)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
            
            # Find elements with both color and background/backgroundColor
            matches = inline_style_regex.finditer(content)
            for m in matches:
                block = m.group(1)
                bg_m = re.search(r"(?:background|backgroundColor):\s*['\"](#?[a-zA-Z0-9_]+)['\"]", block)
                c_m = re.search(r"(?:color):\s*['\"](#?[a-zA-Z0-9_]+)['\"]", block)
                if bg_m and c_m:
                    bg = bg_m.group(1).lower()
                    c = c_m.group(1).lower()
                    if bg.startswith('#') and c.startswith('#'):
                        try:
                            l_bg = get_luminance(*hex_to_rgb(bg))
                            l_c = get_luminance(*hex_to_rgb(c))
                            cr = contrast_ratio(l_bg, l_c)
                            if cr < 4.5:
                                line_no = content[:m.start()].count('\n') + 1
                                suspicious_findings.append((rel_p, line_no, c, bg, cr, block[:80].strip()))
                        except Exception:
                            pass

print(f"Total inline low-contrast pairs (< 4.5:1) found: {len(suspicious_findings)}")
for sf in suspicious_findings:
    print(f" - {sf[0]}:{sf[1]} Color: {sf[2]} on Bg: {sf[3]} -> Ratio: {sf[4]:.2f}:1 | Snippet: {sf[5]}")
