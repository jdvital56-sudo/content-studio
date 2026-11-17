# Договор между заводом и движком

Завод не переписывает движки. Каждый движок подключается тонкой обёрткой, которая понимает этот договор.

## Что завод отдаёт: `job.json`

```json
{
  "job_id": "km-2026-11-18-001",
  "channel": "km",
  "passport": "channels/kosta-method.md",
  "script": {"hook": "...", "voice_text": "...", "captions": ["..."], "cta": "BOTTLE"},
  "format": {"width": 1080, "height": 1920, "max_seconds": 35},
  "language": "en",
  "assets_dir": "jobs/km-2026-11-18-001/assets",
  "out_dir": "jobs/km-2026-11-18-001/out"
}
```

## Что движок возвращает

- `out/final.mp4`.
- `out/meta.json`:

```json
{
  "duration_s": 30.4,
  "voice_words": 44,
  "loudness_lufs": -14.0,
  "subtitle_text": "...",
  "licenses": [{"file": "photo1.jpg", "author": "...", "license": "CC BY-SA 4.0", "source": "https://..."}],
  "engine": "reel-factory",
  "engine_version": "..."
}
```

## Что проверяет завод (не движок)

1. Размер 1080×1920, длительность не больше `max_seconds`.
2. Громкость −14 LUFS ± 1.
3. Субтитры совпадают с озвучкой с точностью до 3%.
4. Слов не больше 1,75 на секунду длительности.
5. Нет чёрных кадров, стоп-кадров и тишины.
6. У каждого фото и звука есть лицензия в `meta.json`.

Не прошёл хотя бы один пункт: статус «Брак», кнопка «Опубликовать» неактивна.

## Движки

| Канал | Движок | Обёртка |
|---|---|---|
| km | reel-factory (`heroine-pose-library/engine/make_reel.py`) | первая, этап 1 |
| wi | stickman-video (Remotion) | вторая |
| hi | yt-factory/studio + cinematic-skill | третья |
