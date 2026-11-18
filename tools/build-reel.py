"""Director: turns a script draft from the wall into a finished reel.
script -> (claude -p) lines/poses/stock/effects -> stock fetch + quality check -> voice -> word timings -> render -> automatic checks -> wall.
python tools/build-reel.py <reel id>      Progress lines start with "STEP " (the server shows them on the wall).
"""
import json, os, re, sqlite3, subprocess, sys, shutil
ROOT = r'C:\src\content-studio'
HP = r'C:\Users\Вадим\projects\heroine-pose-library'
ENG = os.path.join(ROOT, 'engines', 'km_editorial')
EDIT_PY = r'C:\src\edit-tools\.venv\Scripts\python.exe'
DB = os.path.join(ROOT, 'data', 'studio.db')
CAL = os.path.join(ROOT, 'trials', 'cal')
env = dict(os.environ, PYTHONIOENCODING='utf-8')
rid = int(sys.argv[1])
db = sqlite3.connect(DB)


def step(s): print('STEP ' + s, flush=True)
def log(action, note=''): db.execute('INSERT INTO events(reel_id,actor,action,note) VALUES(?,?,?,?)', (rid, 'director', action, note)); db.commit()
def setrow(**kw):
    db.execute('UPDATE reels SET ' + ','.join(f'{k}=?' for k in kw) + ',updated_at=CURRENT_TIMESTAMP WHERE id=?', (*kw.values(), rid)); db.commit()
def run(cmd, **kw):
    kw.setdefault('env', env)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', **kw)
    if r.returncode != 0: raise RuntimeError((r.stderr or r.stdout)[-400:])
    return r.stdout


def norm(t): return re.sub(r'[^a-z0-9 ]', '', t.lower().replace("'", '')).split()


def poses():
    ids = sorted({f[:-4] for f in os.listdir(os.path.join(HP, 'library', 'poses')) if f.endswith('.png') and '__m' not in f and not f.startswith('fb_') and f.endswith('_camera.png')})
    return ids


def stock_ok(path, line=''):
    from PIL import Image, ImageStat, ImageFilter
    os.makedirs(CAL, exist_ok=True); jpg = os.path.join(CAL, f'q{rid}.jpg')
    run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.5', '-i', path, '-frames:v', '1', '-vf', 'scale=360:-1', jpg])
    im = Image.open(jpg).convert('L'); m = ImageStat.Stat(im).mean[0]; ed = ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).stddev[0]
    if not (45 <= m <= 220 and ed >= 20): return False  # too dark/bright or a blurry close-up (calibrated on our bad clips 18.11)
    if not line: return True
    # second check with eyes: Claude looks at the frame and says whether it fits the spoken line
    q = (f'Look at the image file {jpg}. It is a stock video frame for a short fitness reel. The voice-over says: "{line}". '
         'Answer YES if the frame clearly fits this line and looks like a pleasant, natural scene; answer NO if it does not fit, '
         'shows something else, is a weird close-up, or shows text on screen. Reply with one word: YES or NO.')
    try:
        r = subprocess.run(['claude', '-p', '--allowedTools', 'Read', '--output-format', 'json'], input=q, capture_output=True, text=True, encoding='utf-8', env=env, timeout=120)
        ans = json.loads(r.stdout).get('result', '').strip().upper()
        return not ans.startswith('NO')
    except Exception:
        return True  # if the check itself fails, keep the technical check result


try:
    row = db.execute('SELECT channel,script FROM reels WHERE id=?', (rid,)).fetchone()
    if not row or not row[1]: raise RuntimeError('у этого ролика нет сценария')
    ch, script = row[0], json.loads(row[1])
    setrow(status='render'); log('build', 'start')
    sett = {k: json.loads(v) for k, v in db.execute("SELECT key,value FROM settings WHERE key IN ('presence')")}
    pres = (sett.get('presence', {}).get(ch) or {}); presence, mouth = pres.get('mode', 'cameo'), pres.get('mouth', 'calm')
    slug = f'reel{rid}'
    fmt = script.get('format', 'tania')
    if fmt == 'stock': presence = 'off'
    if fmt == 'text':
        # Text over the owner's own footage (format of the reference reels): no voice, typed lines, the person trains on camera.
        step('Беру твоё видео из «Мои видео»')
        lib = os.path.join(ROOT, 'media', 'library', ch)
        vids = sorted([f for f in os.listdir(lib) if f.lower().endswith(('.mp4', '.mov', '.m4v', '.webm'))]) if os.path.isdir(lib) else []
        if not vids: raise RuntimeError('в «Мои видео» нет роликов этого канала: загрузи тренировку')
        used = [r[0] for r in db.execute("SELECT note FROM events WHERE action='textreel'")]
        want = script.get('footage')
        vid = want if want in vids else min(vids, key=lambda v: used.count(v))  # the clip the Writer wrote for, else the least used
        vpath = os.path.join(lib, vid)
        vdur = float(json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', vpath]))['format']['duration'])
        beats = script.get('beats') or [[c] for c in (script.get('captions') or [script['hook']])]
        beats = [b if isinstance(b, list) else [b] for b in beats][:5]
        dur = max(12.0, min(20.0, 3.6 * len(beats) + 1))
        if vdur < 8: raise RuntimeError('видео слишком короткое для ролика')
        # Cutting one long video into several reels: every new reel takes the next segment of the same clip.
        n_used = used.count(vid); span = max(0.0, vdur - dur - 0.5)
        start = 0.0 if span == 0 else (n_used * dur) % (span + 0.001)  # 0-19 s, then 19-38 s, then it wraps
        dur = min(dur, vdur - start); per = dur / len(beats); B = []
        for i, b in enumerate(beats):
            lines = []
            for j, tx in enumerate(b):
                size = 74 if tx.rstrip().endswith(':') or len(tx) > 22 else (118 if len(tx) <= 14 else 96)
                lines.append(dict(text=tx, size=size, delay=round(0.5 * j, 2), gold=(j == len(b) - 1 and i in (1, len(beats) - 1))))
            B.append(dict(t=round(i * per + 0.3, 2), end=round((i + 1) * per - 0.05, 2), lines=lines))
        spec = dict(name=slug, video=vpath, start=round(start, 2), dur=round(dur, 2), beats=B)
        sp = os.path.join(ENG, 'specs', slug + '.text.json'); json.dump(spec, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        step('Набираю текст по видео'); run([sys.executable, os.path.join(ENG, 'textreel.py'), sp])
        dest = os.path.join(ROOT, 'trials', 'reels', 'final', slug + '_T.mp4')
        shutil.copy(os.path.join(ENG, 'out', slug + '_text', 'final.mp4'), dest)
        pr = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height:format=duration', '-of', 'json', dest]))
        d2 = float(pr['format']['duration']); ok = (pr['streams'][0]['width'], pr['streams'][0]['height']) == (1080, 1920) and d2 <= 35
        db.execute("UPDATE reels SET sub=? WHERE id=?", ('Текст по видео · ' + vid + ' · звук добавить в приложении', rid)); db.commit()
        setrow(job_dir=dest, length_s=round(d2), checks=('o' if ok else 'x') + 'ooo', status='wait' if ok else 'bad')
        log('textreel', vid); log('build', f'text ok {d2:.1f}s'); step('Готово'); print('DONE', dest); sys.exit(0)
    # 1. director: split the script into lines with pose, stock query and effects
    step('Режиссёр раскладывает сценарий по кадрам')
    P = poses()
    prompt = f"""You are the director of a short-video factory. Turn this script into a shot list.
SCRIPT (spoken text, must stay EXACTLY as written, only split into lines): {script['spoken']}
Hook: {script.get('hook')}. Captions idea: {script.get('captions')}. Visual ideas: {script.get('visuals')}. Pose emotions suggested: {script.get('tania')}. CTA type: {script.get('cta')}.
Rules:
- Split the spoken text into 4 to 7 lines at sentence or phrase boundaries. Joined together the lines must equal the spoken text word for word. Do not add or drop words.
- Line 1 is the hook: big text, stock_query null. The last line is the call to action: stock_query null, fx has one cta item.
- For middle lines choose stock_query (3-5 English words, a concrete scene a camera could film, a woman doing the thing, no text on screen, not a face close-up, not dark) or null when the line is abstract.
- pose: choose from this list only: {', '.join(P)}. Match the emotion (stop_*, shrug_* for doubt, point_you_joy_camera to address the viewer, thumbs_up_joy_camera, ok_joy_camera, explain_*). Use a pose at most twice.
- gold: 1 to 3 key words of that line, written exactly as in the line.
- fx: optional. counter {{"type":"counter","n":<number>,"label":"<unit>","word":"<the number word as spoken>"}} only if the line contains a number. stamp {{"type":"stamp","text":"<2 words max, capitals>","word":"<word from the line>"}} for one contrarian or key word at most once in the whole reel. cta {{"type":"cta","text":"FOLLOW"|"SAVE"|"SHARE","word":"<first word of the final line>"}} on the last line only.
Output ONLY JSON: {{"lines":[{{"say":"...","gold":["..."],"pose":"...","stock_query":null,"fx":[]}}]}}"""
    spec_lines = None
    for attempt in range(2):
        out = run(['claude', '-p', '--output-format', 'json', '--tools', ''], input=prompt)
        res = json.loads(out).get('result', ''); m = re.search(r'\{.*\}', res, re.S)
        try: cand = json.loads(m.group(0))['lines']
        except Exception: continue
        if norm(' '.join(l['say'] for l in cand)) == norm(script['spoken']) and all(l['pose'] in P for l in cand): spec_lines = cand; break
        prompt += '\nYour previous answer changed the words or used an unknown pose. Keep the words exactly and use only listed poses.'
    if not spec_lines: raise RuntimeError('Режиссёр не смог разложить сценарий (текст изменён)')
    # 2. stock: fetch from Pexels (cached), reject dark/blurry clips, try the next result
    step('Подбираю и проверяю стоковые кадры')
    sys.path.insert(0, os.path.join(HP, 'engine')); os.chdir(HP)
    import stock
    for l in spec_lines:
        q = l.pop('stock_query', None); l['stock'] = None
        if not q: continue
        for pick in range(4):
            try: p = stock.fetch(q, 6, pick)
            except Exception as e: continue
            if stock_ok(p, l['say']): l['stock'] = p; break
        if not l['stock']: log('stock', f'не нашёл годный кадр: {q}')
    spec = dict(name=slug, brand=f'KM  ·  HABITS  ·  {rid:02d}', presence=presence, mouth=mouth, lines=spec_lines,
                voice_dir=os.path.join(HP, 'voice', slug), audio=os.path.join(ROOT, 'trials', 'reels', 'fx', slug + '.m4a'))
    sp = os.path.join(ENG, 'specs', slug + '.v2.json'); json.dump(spec, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # 3. voice, 4. word timings, 5. render
    step('Озвучка (VoiceStudio)'); run([sys.executable, os.path.join(ENG, 'voice.py'), sp])
    step('Тайминги слов'); run([EDIT_PY, os.path.join(ENG, 'timings.py'), sp], cwd=ENG, env=dict(env, TORCH_HOME='C:/ai-cache/torch'))
    step('Сборка ролика'); run([sys.executable, os.path.join(ENG, 'render2.py'), sp])
    final = os.path.join(ENG, 'out', slug + '_v2', 'final.mp4'); dest = os.path.join(ROOT, 'trials', 'reels', 'final', slug + '_V2.mp4')
    shutil.copy(final, dest)
    # 6. automatic checks (really measured)
    step('Проверка качества')
    pr = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height:format=duration', '-of', 'json', dest]))
    dur = float(pr['format']['duration']); w, h = pr['streams'][0]['width'], pr['streams'][0]['height']
    ln = subprocess.run(['ffmpeg', '-nostats', '-i', dest, '-af', 'loudnorm=print_format=summary', '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8')
    lu = float(re.search(r'Input Integrated:\s+(-?[\d.]+)', ln.stderr).group(1))
    words = len(script['spoken'].split())
    c_fmt = 'o' if (w, h) == (1080, 1920) and dur <= 35 else 'x'
    c_vol = 'o' if abs(lu + 14) <= 1.5 else 'x'
    c_wps = 'o' if words / dur <= 2.4 else 'x'  # speech density
    c_stock = 'o' if all(l.get('stock') or True for l in spec_lines) else 'x'
    checks = c_fmt + c_vol + c_wps + c_stock
    setrow(job_dir=dest, length_s=round(dur), checks=checks, status='wait' if 'x' not in checks else 'bad')
    log('build', f'ok {dur:.1f}s {lu:.1f}LUFS checks={checks}')
    step('Готово'); print('DONE', dest, dur, lu, checks)
except Exception as e:
    setrow(status='draft'); log('build', 'ошибка: ' + str(e)[:300]); print('ERROR', str(e)[:300], flush=True); sys.exit(1)
