import os
import re

src_dir = r"frontend\src"

# Scan for small fonts, low contrast text, and headings without explicit contrast
tiny_font_regex = re.compile(r"fontSize:\s*['\"](0\.[5-7]\d*rem|[8-9]px|1[0-1]px)['\"]|text-\[([8-9]px|1[0-1]px)\]")
text_xs_regex = re.compile(r"\btext-xs\b|fontSize:\s*['\"]0\.75rem['\"]")
heading_regex = re.compile(r"<h([1-6])([^>]*)>")

results = {
    "tiny_fonts": [],
    "text_xs_count": 0,
    "headings": []
}

for root, dirs, files in os.walk(src_dir):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            p = os.path.join(root, f)
            rel_p = os.path.relpath(p, src_dir)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                lines = fp.readlines()
            for idx, line in enumerate(lines, 1):
                # Check tiny fonts (< 12px)
                m = tiny_font_regex.search(line)
                if m:
                    results["tiny_fonts"].append((rel_p, idx, m.group(0), line.strip()))
                
                # Check text-xs or 0.75rem
                if text_xs_regex.search(line):
                    results["text_xs_count"] += 1
                
                # Check headings
                for hm in heading_regex.finditer(line):
                    tag = "h" + hm.group(1)
                    attrs = hm.group(2)
                    has_color = ("color" in attrs) or ("text-" in attrs)
                    results["headings"].append((rel_p, idx, tag, has_color, line.strip()))

print(f"Total files checked: {len(results['headings'])}")
print(f"Total headings: {len(results['headings'])}")
no_color_headings = [h for h in results["headings"] if not h[3]]
print(f"Headings without explicit color: {len(no_color_headings)}")
for h in no_color_headings:
    print(f" - {h[0]}:{h[1]} [{h[2]}] -> {h[4][:110]}")

print(f"\nTiny font sizes (< 12px): {len(results['tiny_fonts'])}")
for tf in results["tiny_fonts"][:30]:
    print(f" - {tf[0]}:{tf[1]} [{tf[2]}] -> {tf[3][:110]}")

print(f"\nTotal text-xs / 0.75rem occurrences: {results['text_xs_count']}")
