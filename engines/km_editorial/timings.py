"""Step 1 (needs Whisper): word timings of every voice line -> specs/<name>.timings.json.
Run with the env that has Whisper:  C:/src/edit-tools/.venv/Scripts/python.exe timings.py specs/<name>.json"""
import json, sys, os
import whisper
sp = json.load(open(sys.argv[1], encoding='utf-8'))
m = whisper.load_model('small', download_root='C:/ai-cache/whisper')
out = []
for i, _ in enumerate(sp['lines']):
    r = m.transcribe(os.path.join(sp['voice_dir'], f'line{i}.wav'), word_timestamps=True, language='en', fp16=False)
    out.append([[x['start'], x['end']] for s in r['segments'] for x in s['words']])
json.dump(out, open(sys.argv[1].replace('.v2.json', '.json').replace('.json', '.timings.json'), 'w'))
print('ok', [len(o) for o in out])
