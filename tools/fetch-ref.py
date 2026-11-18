"""Downloads a reference reel for analysis: yt-dlp writes the metadata (video.info.json), curl downloads the media
(Python HTTPS is broken on this machine by antivirus, curl is fine). Own/reference material for style study only.
python tools/fetch-ref.py <folder with video.info.json>  -> <folder>/ref.mp4"""
import json, os, subprocess, sys
d = sys.argv[1]; info = json.load(open(os.path.join(d, 'download', 'video.info.json'), encoding='utf-8'))
F = info.get('formats') or []
prog = [f for f in F if f.get('url') and f.get('format_id') in ('1', '2', '3') and 'vcodec' not in f]
fmts = prog[:1] or [max([f for f in F if f.get('vcodec', 'none') != 'none' and f.get('url')], key=lambda f: int(f.get('width') or 0)), [f for f in F if f.get('acodec', 'none') != 'none' and f.get('vcodec') == 'none'][0]]
parts = []
for i, f in enumerate(fmts):
    p = os.path.join(d, f'part{i}.mp4')
    subprocess.run(['curl', '-s', '-L', '-o', p, f['url']], check=True); parts.append(p)
out = os.path.join(d, 'ref.mp4')
cmd = ['ffmpeg', '-v', 'error', '-y'] + sum([['-i', p] for p in parts], []) + ['-c', 'copy', out]
subprocess.run(cmd, check=True)
for p in parts: os.remove(p)
print(os.path.getsize(out) // 1024, 'KB', info.get('title', '')[:60], '|', info.get('uploader'), '| likes', info.get('like_count'), '| dur', info.get('duration'))
print('DESC:', (info.get('description') or '')[:300].replace('\n', ' '))
