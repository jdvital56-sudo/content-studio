"""Text-over-real-footage reel (the format of the reference reels analysed 18.11): a real person moving, one or two lines of
typed serif text, no voice-over, trending sound added at posting. Needs the person's own footage (Мои видео).
python textreel.py <spec.json>   spec: {name, video, start, dur, beats:[{t, end, lines:[{text, size, color, weight}]}], cta}
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
SERIF = r'C:\Users\Вадим\.claude\skills\effects\fonts\InstrumentSerif-Italic.ttf'
SANS = r'C:\src\arcads-cut\fonts\Montserrat.ttf'
GOLD = (222, 196, 150)
ARG = os.path.abspath(sys.argv[1]); sp = json.load(open(ARG, encoding='utf-8'))
out_dir = os.path.join(os.path.dirname(ARG), '..', 'out', sp['name'] + '_text'); os.makedirs(out_dir, exist_ok=True)


def ease(p): p = max(0.0, min(1.0, p)); return 1 - (1 - p) ** 3
def serif(size): return ImageFont.truetype(SERIF, size)
def sans(size):
    f = ImageFont.truetype(SANS, size)
    try: f.set_variation_by_axes([800])
    except Exception: pass
    return f


top = Image.new('RGBA', (W, 900), (0, 0, 0, 0)); td = ImageDraw.Draw(top)
for y in range(900): td.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * (1 - y / 900) ** 1.6)))  # soft shade for legibility
dur = sp['dur']; nfr = int(dur * FPS)
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(sp['start']), '-t', str(dur), '-i', sp['video'], '-vf', f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}',
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
audio = os.path.join(out_dir, 'a.m4a')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(sp['start']), '-t', str(dur), '-i', sp['video'], '-vn', '-af', 'loudnorm=I=-14:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', audio], check=True)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', audio, '-c:v', 'libx264', '-crf', '18',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', os.path.join(out_dir, 'final.mp4')], stdin=subprocess.PIPE)
stills = [float(s) for s in os.environ.get('KM_STILLS', '').split(',') if s]
for fi in range(nfr):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: break
    t = fi / FPS
    if stills and not any(abs(t - s) < 0.5 / FPS for s in stills): continue
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA'); fr.alpha_composite(top, (0, 0)); d = ImageDraw.Draw(fr)
    for b in sp['beats']:
        if not (b['t'] <= t < b['end']): continue
        y = 210; fade = ease((b['end'] - t) / 0.25)
        for ln in b['lines']:
            size = ln.get('size', 96); f = sans(size) if ln.get('sans') else serif(size)
            n = len(ln['text']); shown = int(min(n, max(0, (t - b['t'] - ln.get('delay', 0)) * 26)))
            txt = ln['text'][:shown]
            col = GOLD if ln.get('gold') else (255, 255, 255)
            if txt:
                lay = Image.new('RGBA', (W, size * 2), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                ld.text((62, 8), txt + ('|' if shown < n else ''), font=f, fill=(0, 0, 0, int(140 * fade)))      # shadow
                ld.text((60, 4), txt + ('|' if shown < n else ''), font=f, fill=col + (int(255 * fade),))
                fr.alpha_composite(lay, (0, y))
            y += int(size * 1.08)
    if stills: fr.convert('RGB').resize((360, 640)).save(os.path.join(out_dir, f'still_{t:.1f}.png')); continue
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
print('OK', os.path.join(out_dir, 'final.mp4'))
