import re
import os

with open('docs/manual/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
print(f'Total images found in index.html: {len(images)}')
missing = []
for src in images:
    img_path = os.path.normpath(os.path.join('docs/manual', src))
    if not os.path.exists(img_path):
        missing.append((src, img_path))

if missing:
    print(f'Missing images: {missing}')
else:
    print('All referenced images exist on disk!')
