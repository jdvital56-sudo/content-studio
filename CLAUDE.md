# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State

Nothing is built yet. Read in this order: [DECISIONS.md](DECISIONS.md) (what the owner settled, do not re-ask), [PLAN.md](PLAN.md) (current phase), [RISKS.md](RISKS.md). After any decision or finished step, update those files in the same commit. The owner reads them in Russian, so keep them in Russian.

## Rules specific to this project

- **Nothing publishes and nothing spends money without the owner's button.** Agents never publish, approve, or reply to comments on their own.
- **The engines are not rewritten.** Each engine is wrapped: the factory writes `job.json`, the engine returns `final.mp4` + `meta.json`. Engines today:
  - reel-factory: `C:\Users\Вадим\projects\heroine-pose-library\engine\make_reel.py` (skill `reel-factory`)
  - stickmen (Remotion): `C:\Users\Вадим\projects\stickman-video` (read `SCRIPT-RULES.md`)
  - documentaries: `C:\Users\Вадим\projects\yt-factory\studio`
  - arcads-cut: `C:\src\arcads-cut` (needs `ARCADS_CYR=1`, `ARCADS_FIT=1`)
- **Media never goes into git** (mp4, wav, images, renders). Finished videos go to Backblaze B2.
- **Secrets** (B2 key, Telegram token, Claude token) are entered by the owner himself into files outside git, never through chat.
- The web app listens on `127.0.0.1` only. Phone access later through Tailscale, not by opening ports.
- Scripts are written with `claude -p` on the owner's subscription, not an API key and not DeepSeek. The token lives in one place so it can be swapped for the factory's own account.
- No metadata spoofing, no duplicate-hiding, no account farms ("uniqualizer" = honest A/B variants).

## Machine traps

- Cyrillic in `C:\Users\Вадим` breaks Dart, arcads-cut, the effects skill. Keep this project under `C:\src`.
- Default `python` on PATH is the Hermes venv. Use this project's own venv.
- Avast intercepts HTTPS from Python: "service not responding" means check certificates first (truststore). curl works.
- Disk C had 20.5 GB free on 17.11.2026. Check free space before any batch render.
- The PC does not sleep on mains (powercfg AC = 0) but does on battery after 10 min.

## Checking work

A fix to any threshold (silence cut, hook score, quality gate) is tested against a table of real cases from the owner, both what must now work and what must still work. Videos are checked by numbers and frames before being shown.
