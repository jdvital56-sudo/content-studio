"""KM Editorial v2: stock window + cartoon Tania from the pose library (poses, moving mouth) + effects.
Layout 1080x1920: brand line + progress bar on top, stock window (or big kinetic headline) in the top zone,
caption bottom-left, Tania cut-out bottom-right standing behind a gold ledge. Words appear as they are spoken.
Run (default python with Pillow):  python render2.py specs/<name>.v2.json     (needs specs/<name>.timings.json from timings.py)
KM_STILLS=1.0,5.2 python render2.py ...  saves those times as small PNGs for a quick look.
"""
import array, glob, json, math, os, shutil, subprocess, sys, tempfile, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ARG = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ''  # absolute before we chdir to the pose library
HERE = os.path.dirname(os.path.abspath(__file__))
HP = r'C:\Users\Вадим\projects\heroine-pose-library'
sys.path.insert(0, os.path.join(HP, 'engine')); os.chdir(HP)
import render_scene as rs  # mouth_track, read_wav
import mouth as mouthlib   # compose(pose, level): pose with closed / half / open mouth

W, H, FPS = 1080, 1920, 30
PAPER, GRID, INK, GOLD, GOLD_T, WHITE = (250, 247, 242), (231, 220, 203), (29, 29, 31), (201, 171, 124), (138, 108, 63), (255, 255, 255)
FONT = r'C:\src\arcads-cut\fonts\Montserrat.ttf'
PAD = 0.35
CARD = (900, 700); CARD_XY = (90, 190)
TANIA_H = 820; LEDGE_Y = 1690


def font(size, weight=700):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f


def ease(p):
    p = max(0.0, min(1.0, p)); return 1 - (1 - p) ** 3


def clamp(v): return max(0.0, min(1.0, v))


def wav_dur(p):
    with wave.open(p) as w: return w.getnframes() / w.getframerate()


def spread(text, asr):
    toks = text.split()
    if not asr: return [(t, 0, 0.5) for t in toks]
    t0, t1 = asr[0][0], asr[-1][1]
    lens = [len(t) + 1 for t in toks]; tot = sum(lens); acc = 0; res = []
    for t, l in zip(toks, lens):
        res.append((t, t0 + (t1 - t0) * acc / tot, t0 + (t1 - t0) * (acc + l) / tot)); acc += l
    return res


def layout(words, size, maxw, fnt):
    d = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    sp = d.textlength(' ', font=fnt); x = y = 0; lh = int(size * 1.12); out = []
    for wd in words:
        w = d.textlength(wd, font=fnt)
        if x and x + w > maxw: x = 0; y += lh
        out.append((wd, x, y, w)); x += w + sp
    return out, y + lh


def base_bg(brand):
    im = Image.new('RGB', (W, H), PAPER); d = ImageDraw.Draw(im)
    for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=GRID, width=1)
    f = font(32, 700); x = 90
    for ch in brand:
        d.text((x, 78), ch, font=f, fill=GOLD_T); x += d.textlength(ch, font=f) + 4
    d.line([(90, 140), (W - 90, 140)], fill=GRID, width=4)
    return im


_pose_cache = {}
def tania(pose, lvl):
    k = (pose, lvl)
    if k not in _pose_cache:
        im = mouthlib.compose(pose, lvl)
        s = TANIA_H / im.height
        _pose_cache[k] = im.resize((int(im.width * s), TANIA_H), Image.LANCZOS)
    return _pose_cache[k]


def rounded_mask(w, h, r):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); return m


def stamp_img(text):
    f = font(60, 800); d = ImageDraw.Draw(Image.new('RGB', (10, 10))); tw = int(d.textlength(text, font=f))
    im = Image.new('RGBA', (tw + 80, 130), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([4, 4, im.width - 5, im.height - 5], 18, fill=(250, 247, 242, 235), outline=GOLD_T + (255,), width=8)
    dd.text((40, 24), text, font=f, fill=GOLD_T + (255,))
    return im.rotate(8, expand=True, resample=Image.BICUBIC)


def main(spec_path):
    sp = json.load(open(spec_path, encoding='utf-8')); name = sp['name']
    timings = json.load(open(spec_path.replace('.v2.json', '.timings.json')))
    out_dir = os.path.join(HERE, 'out', name + '_v2'); os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='kmv2_')
    t0 = 0.0; units = []; mouth = {}
    for i, ln in enumerate(sp['lines']):
        wav = os.path.join(sp['voice_dir'], f'line{i}.wav'); d = wav_dur(wav)
        ws = spread(ln['say'], timings[i])
        rate, data = rs.read_wav(wav)
        mouth.update(rs.mouth_track(rate, data, FPS, int((t0 + d + PAD) * FPS) + 5, t0))
        units.append(dict(i=i, start=t0, end=t0 + d + PAD, dur=d + PAD, say=ln['say'], gold=[g.lower() for g in ln.get('gold', [])],
                          words=[(w, t0 + a, t0 + b) for w, a, b in ws], pose=ln.get('pose', 'stand_joy_camera'),
                          stock=ln.get('stock'), fx=ln.get('fx', []), cta=ln.get('cta')))
        t0 += d + PAD
    total = t0; nfr = int(math.ceil(total * FPS))
    bg = base_bg(sp.get('brand', 'KM  ·  HABITS'))
    cardmask = rounded_mask(*CARD, 44)
    for u in units:
        toks = [w for w, _, _ in u['words']]
        if u['stock']:  # caption bottom-left, narrow
            size, maxw, maxh = 66, 470, 700
            for size in (66, 58, 52, 46):
                fnt = font(size, 800); lay, hgt = layout(toks, size, maxw, fnt)
                if hgt <= maxh: break
        else:           # big headline in the top zone
            maxw = 900
            for size in (132, 118, 104, 92, 80):
                fnt = font(size, 800); lay, hgt = layout(toks, size, maxw, fnt)
                if hgt <= 640: break
        u.update(font=fnt, lay=lay, h=hgt, size=size)
        if u['stock']:  # frames of the stock clip for the whole line
            clip = glob.glob(os.path.join(HP, 'library', 'stock', u['stock'] + '*.mp4'))[0]
            fd = os.path.join(tmp, f'l{u["i"]}'); os.makedirs(fd)
            subprocess.run(['ffmpeg', '-v', 'error', '-stream_loop', '-1', '-i', clip, '-t', f'{u["dur"] + 0.3:.2f}', '-vf', f'fps={FPS},scale=980:790:force_original_aspect_ratio=increase,crop=980:790', '-q:v', '3', os.path.join(fd, '%04d.jpg')], check=True)
            u['fd'] = fd
        for fx in u['fx']:
            fx['t'] = next((ws for w, ws, we in u['words'] if w.lower().strip('.,?!:;"“”') == fx.get('word', '').lower()), u['start'] + 0.3)
            if fx['type'] == 'stamp': fx['img'] = stamp_img(fx['text'])
    audio = sp['audio']
    stills = [float(s) for s in os.environ.get('KM_STILLS', '').split(',') if s]
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', audio,
           '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', os.path.join(out_dir, 'raw.mp4')]
    pipe = None if stills else subprocess.Popen(cmd, stdin=subprocess.PIPE)
    last_pose = None; pose_t = 0.0
    for fi in (sorted({int(s * FPS) for s in stills}) if stills else range(nfr)):
        t = fi / FPS; fr = bg.convert('RGBA'); d = ImageDraw.Draw(fr)
        u = next((x for x in units if x['start'] <= t < x['end']), units[-1]); lt = t - u['start']
        # progress bar under the brand line
        d.line([(90, 140), (90 + int((W - 180) * clamp(t / total)), 140)], fill=GOLD, width=4)
        fade = ease((u['end'] - t) / 0.12) if u is not units[-1] else 1.0
        # --- top zone: stock window or big headline
        if u['stock']:
            fi_in = max(1, min(int(lt * FPS) + 1, len(os.listdir(u['fd']))))
            im = Image.open(os.path.join(u['fd'], f'{fi_in:04d}.jpg')).convert('RGB')
            z = 1.0 + 0.06 * clamp(lt / u['dur']); cw, ch = int(980 / z), int(790 / z)
            im = im.crop(((980 - cw) // 2, (790 - ch) // 2, (980 - cw) // 2 + cw, (790 - ch) // 2 + ch)).resize((980, 790), Image.BILINEAR)
            im = im.crop((40, 45, 940, 745))
            p = ease(lt / 0.3); wmask = cardmask.copy()
            if p < 1:
                wmask = Image.composite(wmask, Image.new('L', CARD, 0), Image.new('L', CARD, 0))
                m2 = Image.new('L', CARD, 0); ImageDraw.Draw(m2).rectangle([0, 0, int(CARD[0] * p), CARD[1]], fill=255)
                wmask = Image.composite(cardmask, Image.new('L', CARD, 0), m2)
            sh = Image.new('RGBA', (CARD[0] + 80, CARD[1] + 80), (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle([40, 52, 40 + CARD[0], 52 + CARD[1]], 44, fill=(60, 45, 20, 55))
            fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (CARD_XY[0] - 40, CARD_XY[1] - 40))
            fr.paste(im, CARD_XY, wmask)
        # --- words (headline for text lines, caption for stock lines)
        layer = Image.new('RGBA', (W, 900), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        ox = 90
        for (wd, x, y, w), (_, ws, we) in zip(u['lay'], u['words']):
            if t < ws - 0.02: continue
            a = ease((t - ws + 0.02) / 0.16); rise = int((1 - a) * 22)
            gold = wd.lower().strip('.,?!:;"“”') in u['gold']
            if gold:
                pw = clamp((t - ws) / 0.28); by = int(10 + y + u['size'] * 1.02 + rise)
                ld.rectangle([int(ox + x), by, int(ox + x + w * pw), by + 14], fill=GOLD + (int(255 * fade),))
            tmpw = Image.new('RGBA', (int(w) + 20, int(u['size'] * 1.4)), (0, 0, 0, 0))
            ImageDraw.Draw(tmpw).text((0, 0), wd, font=u['font'], fill=(GOLD_T if gold else INK) + (int(255 * a * fade),))
            layer.alpha_composite(tmpw, (int(ox + x), int(10 + y + rise)))
        if u['stock']: fr.alpha_composite(layer, (0, 930))
        else: fr.alpha_composite(layer, (0, 190 + max(0, (700 - u['h']) // 2)))
        # --- effects
        for fx in u['fx']:
            if t < fx['t']: continue
            ft = t - fx['t']
            if fx['type'] == 'stamp':
                s = 1.0 + 0.6 * (1 - ease(ft / 0.18)); a = ease(ft / 0.12)
                im = fx['img']; im2 = im.resize((int(im.width * s), int(im.height * s)), Image.BICUBIC)
                im2.putalpha(im2.getchannel('A').point(lambda v: int(v * a * fade)))
                fr.alpha_composite(im2, (int(560 - im2.width / 2 + 160), int(250 - im2.height / 2 + 80)))
            elif fx['type'] == 'counter':
                n = int(round(fx['n'] * ease(ft / 0.8))); a = ease(ft / 0.2)
                cd = Image.new('RGBA', (360, 190), (0, 0, 0, 0)); cdd = ImageDraw.Draw(cd)
                cdd.rounded_rectangle([0, 0, 359, 189], 32, fill=(255, 255, 255, int(245 * a * fade)), outline=GOLD + (int(255 * a * fade),), width=5)
                cdd.text((30, 14), str(n), font=font(110, 800), fill=GOLD_T + (int(255 * a * fade),))
                cdd.text((30 + (100 if n >= 10 else 60), 74), fx.get('label', ''), font=font(40, 700), fill=INK + (int(255 * a * fade),))
                fr.alpha_composite(cd, (120, 700 - int((1 - a) * 40)))
            elif fx['type'] == 'cta':
                a = ease(ft / 0.3); pill = Image.new('RGBA', (480, 120), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
                pd.rounded_rectangle([0, 0, 479, 119], 60, fill=GOLD + (int(255 * a),))
                pulse = 1 + 0.03 * math.sin(ft * 6)
                txt = f'DM  “{fx["text"]}”'; f2 = font(46, 800); tw = pd.textlength(txt, font=f2)
                pd.text(((480 - tw) / 2, 32), txt, font=f2, fill=INK + (int(255 * a),))
                pill = pill.resize((int(480 * pulse), int(120 * pulse)))
                fr.alpha_composite(pill, (90, 1180 + int((1 - a) * 40)))
        # --- Tania: cut-out, mouth follows the voice, small pop when the pose changes
        if u['pose'] != last_pose: last_pose = u['pose']; pose_t = t
        lvl = mouth.get(fi, 0)
        im = tania(u['pose'], lvl)
        pop = 1.0 + 0.045 * (1 - ease((t - pose_t) / 0.18))
        if pop > 1.001: im = im.resize((int(im.width * pop), int(im.height * pop)), Image.BILINEAR)
        bob = int(5 * math.sin(t * 2.4))
        fr.alpha_composite(im, (int(1085 - im.width), int(LEDGE_Y - im.height + bob + 6)))
        # gold ledge: she stands behind it
        d = ImageDraw.Draw(fr)
        d.rounded_rectangle([60, LEDGE_Y - 4, 1020, LEDGE_Y + 44], 24, fill=PAPER + (255,), outline=GOLD + (255,), width=4)
        if stills: fr.convert('RGB').resize((360, 640)).save(os.path.join(out_dir, f'still_{fi / FPS:.1f}.png')); continue
        pipe.stdin.write(fr.convert('RGB').tobytes())
    if stills: print('stills', out_dir); shutil.rmtree(tmp, ignore_errors=True); return
    pipe.stdin.close(); pipe.wait()
    final = os.path.join(out_dir, 'final.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(out_dir, 'raw.mp4'), '-c:v', 'copy', '-af', 'loudnorm=I=-14:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', final], check=True)
    lic = [dict(file=os.path.basename(g), license='Pexels License', source='pexels.com') for u in units if u['stock'] for g in glob.glob(os.path.join(HP, 'library', 'stock', u['stock'] + '*.mp4'))]
    json.dump(dict(duration_s=round(total, 2), engine='km_editorial v2', licenses=lic + [dict(file='tania pose library', license='own brand asset', source='heroine-pose-library')]), open(os.path.join(out_dir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    shutil.rmtree(tmp, ignore_errors=True); print('OK', final, round(total, 1), 's')


if __name__ == '__main__':
    main(ARG)
