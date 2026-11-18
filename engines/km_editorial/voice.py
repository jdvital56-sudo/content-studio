"""Voice for a KM Editorial reel: one wav per line via VoiceStudio (same voice 'Cat' as reel-factory), then one audio track
with the same 0.35 s pauses the renderer assumes.  python voice.py specs/<name>.v2.json   (VoiceStudio must be running)"""
import json, os, subprocess, sys
HP = r'C:\Users\Вадим\projects\heroine-pose-library'
ARG = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(HP, 'engine')); os.chdir(HP)
import voicestudio, stress

sp = json.load(open(ARG, encoding='utf-8'))
os.makedirs(sp['voice_dir'], exist_ok=True)
wavs = []
for i, ln in enumerate(sp['lines']):
    wav = os.path.join(sp['voice_dir'], f'line{i}.wav'); wavs.append(wav)
    if os.path.exists(wav): continue
    voiced, _, unresolved, _ = stress.prepare(ln['say'], 'en')
    for src, dst in sp.get('spoken', {}).items(): voiced = voiced.replace(src, dst)
    voicestudio.generate(voiced, 'en', sp.get('profile', '57f59979'), wav)
    print('voice', i, 'unresolved', unresolved, flush=True)
cmd = ['ffmpeg', '-v', 'error', '-y']
for w in wavs: cmd += ['-i', w]
fl = ''.join(f'[{k}:a]apad=pad_dur=0.35[a{k}];' for k in range(len(wavs))) + ''.join(f'[a{k}]' for k in range(len(wavs))) + f'concat=n={len(wavs)}:v=0:a=1[o]'
cmd += ['-filter_complex', fl, '-map', '[o]', '-c:a', 'aac', '-b:a', '192k', sp['audio']]
subprocess.run(cmd, check=True); print('audio ok', sp['audio'])
