"""Collects every Russian text fragment of the interface (app/index.html) into i18n/ru-keys.json.
Numbers are normalised to {n} so one key covers "из 20" and "из 7". Re-run after UI text changes, then run i18n-translate.py."""
import json, re, os
ROOT = r'C:\src\content-studio'
src = open(os.path.join(ROOT, 'app', 'index.html'), encoding='utf-8').read()
parts = re.split(r'<[^>]*>|`|\$\{|\}|"|\'|\\n|[{};=]', src)  # tags, template/quote boundaries and code punctuation
keys = []
for p in parts:
    t = re.sub(r'\s+', ' ', p).strip()
    if not t or not re.search(r'[А-Яа-яЁё]', t) or len(t) < 2: continue
    if re.search(r'[a-zA-Z_$]\w*\(|=>|\.\w+\(', t): continue   # code, not text
    t = re.sub(r'\d+(?:[.,]\d+)?', '{n}', t)
    if t not in keys: keys.append(t)
os.makedirs(os.path.join(ROOT, 'app', 'i18n'), exist_ok=True)
json.dump(keys, open(os.path.join(ROOT, 'app', 'i18n', 'ru-keys.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(keys), 'фрагментов')
