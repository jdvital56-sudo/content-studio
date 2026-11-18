"""KM Editorial reel renderer (style: channels/kosta-method.md, STYLE-KM-EDITORIAL.md).
Paper + grid, one gold accent, Montserrat, words appear as they are spoken, cartoon Tania cameo card.
No stock footage, no generated heroine. Engine contract: docs/ENGINE-CONTRACT.md (reads a spec, writes final.mp4 + meta.json).

python render.py specs/<name>.json
"""
import json, math, os, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
PAPER, GRID, INK, GOLD, GOLD_T = (250, 247, 242), (231, 220, 203), (29, 29, 31), (201, 171, 124), (138, 108, 63)
FONT = r'C:\src\arcads-cut\fonts\Montserrat.ttf'
TANIA = r'C:\src\kosta-method-app\assets\mascot\tania-canon.png'
PAD = 0.35  # pause after each voice line in reel-factory's timeline


def font(size, weight=700):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f


def ease(p):  # cubic ease-out, no springs (style rule)
    p = max(0.0, min(1.0, p)); return 1 - (1 - p) ** 3


def wav_dur(p):
    with wave.open(p) as w: return w.getnframes() / w.getframerate()


def line_words(wav, text, asr):
    """Relative start/end of each script word: Whisper span of the line (timings.py) spread over the script words."""
    toks = text.split()
    if not asr: d = wav_dur(wav); asr = [(0, d)]
    t0, t1 = asr[0][0], asr[-1][1]
    n = len(toks); out = []
    for i, tk in enumerate(toks):  # proportional by character length inside the spoken span
        out.append(tk)
    lens = [len(t) + 1 for t in toks]; tot = sum(lens); acc = 0; res = []
    for t, l in zip(toks, lens):
        res.append((t, t0 + (t1 - t0) * acc / tot, t0 + (t1 - t0) * (acc + l) / tot)); acc += l
    return res


def layout(words, size, maxw, fnt):
    """Greedy word wrap. Returns [(word, x, y, w)] and block height."""
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
    f = font(32, 700); sp = 4; x = 90
    for ch in brand:
        d.text((x, 78), ch, font=f, fill=GOLD_T); x += d.textlength(ch, font=f) + sp
    d.line([(90, 140), (W - 90, 140)], fill=GOLD, width=4)
    return im


def tania_card():
    card_w, card_h, r = 900, 806, 48
    sh = Image.new('RGBA', (card_w + 120, card_h + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([60, 70, 60 + card_w, 70 + card_h], r, fill=(60, 45, 20, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    card = Image.new('RGBA', (card_w, card_h), (255, 255, 255, 255))
    t = Image.open(TANIA).convert('RGB'); t = t.crop((0, 0, t.width, int(t.height * 0.62)))
    s = (card_h - 20) / t.height; t = t.resize((int(t.width * s), int(t.height * s)), Image.LANCZOS)
    card.paste(t, ((card_w - t.width) // 2, 10))
    mask = Image.new('L', (card_w, card_h), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w - 1, card_h - 1], r, fill=255)
    card.putalpha(mask)
    return sh, card


def main(spec_path):
    sp = json.load(open(spec_path, encoding='utf-8'))
    name = sp['name']; out_dir = os.path.join(HERE, 'out', name); os.makedirs(out_dir, exist_ok=True)
    timings = json.load(open(spec_path.replace('.json', '.timings.json')))
    # timeline of lines (same arithmetic as reel-factory: duration + PAD)
    t0 = 0.0; units = []
    for i, ln in enumerate(sp['lines']):
        wav = os.path.join(sp['voice_dir'], f'line{i}.wav'); d = wav_dur(wav)
        ws = line_words(wav, ln['say'], timings[i])
        units.append(dict(start=t0, end=t0 + d + PAD, say=ln['say'], gold=[g.lower() for g in ln.get('gold', [])], words=[(w, t0 + a, t0 + b) for w, a, b in ws]))
        t0 += d + PAD
    total = t0
    cameo = [tuple(c) for c in sp.get('cameo', [[0, 2.2], [total - 3.4, total]])]
    bg = base_bg(sp.get('brand', 'KM  ·  HABITS'))
    shadow, card = tania_card()
    # pre-layout every unit
    for u in units:
        toks = [w for w, _, _ in u['words']]
        for size in (132, 118, 104, 92, 80, 70):
            fnt = font(size, 800); lay, hgt = layout(toks, size, W - 180, fnt)
            if hgt <= 600: break
        u['font'], u['lay'], u['h'], u['size'] = fnt, lay, hgt, size
    audio = sp['audio']
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', audio,
           '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', os.path.join(out_dir, 'raw.mp4')]
    stills = [float(s) for s in os.environ.get('KM_STILLS', '').split(',') if s]  # quick check: save these times as PNG and stop
    pipe = None if stills else subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nfr = int(math.ceil(total * FPS))
    cta = sp.get('cta')
    for fi in (sorted({int(s * FPS) for s in stills}) if stills else range(nfr)):
        t = fi / FPS; fr = bg.convert('RGBA')
        # cameo card slide (up from below the frame), 0.35 s each way
        cy = None; cardp = 0.0
        for a, b in cameo:
            if a - 0.01 <= t <= b + 0.01:
                p = min(ease((t - a) / 0.35), ease((b - t) / 0.35)); cy = 884 + int((1 - p) * 900); cardp = p
        if cy is not None:
            sway = int(6 * math.sin(t * 2.2))
            fr.alpha_composite(shadow, (30, cy - 60 + sway)); fr.alpha_composite(card, (90, cy + sway))
        # headline of the current unit
        u = next((x for x in units if x['start'] <= t < x['end']), units[-1])
        layer = Image.new('RGBA', (W, 640), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        for (wd, x, y, w), (_, ws, we) in zip(u['lay'], u['words']):
            if t < ws - 0.02: continue
            a = ease((t - ws + 0.02) / 0.16); rise = int((1 - a) * 22)
            is_gold = wd.lower().strip('.,?!:;"“”') in u['gold']
            col = GOLD_T if is_gold else INK
            if is_gold:  # gold bar wipes in under the key word
                pw = min(1.0, max(0.0, (t - ws) / 0.28))
                by = int(10 + y + u['size'] * 1.02 + rise)
                ld.rectangle([int(90 + x), by, int(90 + x + w * pw), by + 16], fill=GOLD + (255,))
            tmp = Image.new('RGBA', (int(w) + 20, int(u['size'] * 1.4)), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((0, 0), wd, font=u['font'], fill=col + (int(255 * a),))
            layer.alpha_composite(tmp, (int(90 + x), int(10 + y + rise)))
        # knife exit: a gold line crosses and the block collapses onto it
        kt = (t - (u['end'] - 0.22)) / 0.2
        if kt > 0 and u is not units[-1]:
            p = ease(kt); hh = max(2, int(u['h'] * (1 - p)))
            blk = layer.crop((0, 0, W, u['h'] + 20)).resize((W, hh)); layer = Image.new('RGBA', (W, 640), (0, 0, 0, 0))
            cyl = 10 + u['h'] // 2; layer.alpha_composite(blk, (0, cyl - hh // 2))
            ImageDraw.Draw(layer).rectangle([90, cyl - 3, 90 + int((W - 180) * p), cyl + 3], fill=GOLD + (255,))
        # with the cameo card on screen the text sits at the top; without it, it settles toward the middle of the frame
        free = max(0, (1020 - u['h']) // 2)
        fr.alpha_composite(layer, (0, 230 + int(free * (1 - cardp))))
        # CTA pill on the last unit
        if cta and u is units[-1] and t >= u['start'] + 0.2:
            pa = ease((t - u['start'] - 0.2) / 0.3)
            pill = Image.new('RGBA', (900, 120), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
            pd.rounded_rectangle([0, 0, 899, 119], 60, fill=GOLD + (int(255 * pa),))
            txt = f'DM  “{cta}”'; f2 = font(54, 800); tw = pd.textlength(txt, font=f2)
            pd.text(((900 - tw) / 2, 28), txt, font=f2, fill=INK + (int(255 * pa),))
            fr.alpha_composite(pill, (90, 730 + int((1 - pa) * 40)))
        if stills: fr.convert('RGB').resize((360, 640)).save(os.path.join(out_dir, f'still_{fi / FPS:.1f}.png')); continue
        pipe.stdin.write(fr.convert('RGB').tobytes())
    if stills: print('stills', out_dir); return
    pipe.stdin.close(); pipe.wait()
    final = os.path.join(out_dir, 'final.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(out_dir, 'raw.mp4'), '-c:v', 'copy', '-af', 'loudnorm=I=-14:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', final], check=True)
    json.dump(dict(duration_s=round(total, 2), engine='km_editorial', style='KM Editorial', voice_words=sum(len(u['words']) for u in units),
                   licenses=[dict(file='tania-canon.png', license='own brand asset', source='kosta-method-app')]), open(os.path.join(out_dir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('OK', final, round(total, 1), 's')


if __name__ == '__main__':
    main(sys.argv[1])
