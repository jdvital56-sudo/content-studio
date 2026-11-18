"""Translates app/i18n/ru-keys.json into one dictionary per language with `claude -p` (subscription).
python tools/i18n-translate.py uk en        Adding Turkish or Spanish later: python tools/i18n-translate.py tr es  (and add them to LANGS in app/i18n.js)"""
import json, os, re, subprocess, sys
ROOT = r'C:\src\content-studio'
NAMES = {'uk': 'Ukrainian', 'en': 'English', 'tr': 'Turkish', 'es': 'Spanish'}
GLOSS = ('Glossary (use consistently): стена/монтажная стена = Wall; ролик = reel; хук = hook; паспорт канала = channel passport; '
         'образ (Тани) = look; навык = skill; Режиссёр = Director; Писатель = Writer; Критик = Critic; Упаковщик = Packager; Продюсер = Producer; '
         'корзина = Trash; "Ждёт тебя" = Needs you (a queue); сток = stock footage; героиня/Таня = the host Tania (keep the name Tania/Таня in Ukrainian); '
         'пакет для публикации = publishing pack; автопубликация = auto-publishing; Диск = Google Drive. Keep brand and product names unchanged (Kosta Method, What if, KM Editorial, Instagram, TikTok, YouTube, Whisper, Pexels, Flow, fal).')
keys = json.load(open(os.path.join(ROOT, 'app', 'i18n', 'ru-keys.json'), encoding='utf-8'))
env = dict(os.environ, PYTHONIOENCODING='utf-8')
for lang in sys.argv[1:]:
    out_path = os.path.join(ROOT, 'app', 'i18n', f'{lang}.json')
    done = json.load(open(out_path, encoding='utf-8')) if os.path.exists(out_path) else {}
    todo = [k for k in keys if k not in done]
    for i in range(0, len(todo), 60):
        batch = todo[i:i + 60]
        prompt = (f'Translate these user-interface strings from Russian to {NAMES[lang]}. They are fragments of a video-production app, '
                  f'short and natural, in the style of Apple interface text (clear, friendly, no jargon). Keep the placeholder {{n}} exactly where a number goes, '
                  f'keep punctuation and symbols (→ ✓ … ·), keep capitalisation style. {GLOSS}\n'
                  f'Return ONLY a JSON array of {len(batch)} strings, in the same order, no comments.\n' + json.dumps(batch, ensure_ascii=False))
        for attempt in range(3):
            r = subprocess.run(['claude', '-p', '--output-format', 'json', '--tools', ''], input=prompt, capture_output=True, text=True, encoding='utf-8', env=env)
            try:
                res = json.loads(r.stdout)['result']; arr = json.loads(re.search(r'\[.*\]', res, re.S).group(0))
                if len(arr) == len(batch): break
            except Exception: pass
            arr = None
        if not arr: print('batch failed', lang, i); continue
        for k, v in zip(batch, arr):
            if '{n}' in k and '{n}' not in v: continue  # placeholder lost: keep Russian rather than a wrong number
            done[k] = v
        json.dump(done, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(lang, i + len(batch), '/', len(todo), flush=True)
print('done')
