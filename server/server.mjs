// Content Studio: local server. Listens on 127.0.0.1 only (see CLAUDE.md).
// Serves the wall (app/) and a small JSON API over SQLite (node:sqlite, built into Node).
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { homedir } from 'node:os';
import { DatabaseSync } from 'node:sqlite';
import { dirname, join, extname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
await mkdir(join(root, 'data'), { recursive: true });
const db = new DatabaseSync(join(root, 'data', 'studio.db'));

db.exec(`
CREATE TABLE IF NOT EXISTS reels(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  channel TEXT NOT NULL,
  title TEXT NOT NULL,
  sub TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'draft',
  length_s INTEGER DEFAULT 0,
  checks TEXT DEFAULT 'nnnn',
  job_dir TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reel_id INTEGER, actor TEXT, action TEXT, note TEXT,
  at TEXT DEFAULT CURRENT_TIMESTAMP
);`);

try { db.exec('ALTER TABLE reels ADD COLUMN base_path TEXT'); } catch {}
// Effects that work on stock footage without a face (see app Skills page). Face-bound ones are not allowed here.
const FX_OK = new Set(['reject-stamp', 'tap', 'countdown-flip', 'moody', 'scribble', 'rabbit-hole', 'dot-reveal', 'headline-box']);
const FX_PY = join(homedir(), '.claude', 'skills', 'effects', '.venv', 'Scripts', 'python.exe');
const FX_SCRIPT = join(homedir(), '.claude', 'skills', 'effects', 'scripts', 'fx.py');
// Effects whose built-in text/author names (e.g. "Vibha", "Claude", "197K") we must replace first; not applied manually yet.
const DENY = new Set(['comment-box','glass-widgets','pastel-word','checklist','headline-wall','liquid-glass-graph','over-the-shoulder-zoom','match-cut','tier-list','cover-star']);
const jobs = new Map();
const STATUSES =new Set(['draft','render','check','wait','ok','pub','bad']);
const log = (reel, actor, action, note = '') =>
  db.prepare('INSERT INTO events(reel_id,actor,action,note) VALUES(?,?,?,?)').run(reel, actor, action, note);

if (db.prepare('SELECT COUNT(*) c FROM reels').get().c === 0) {
  const seed = db.prepare('INSERT INTO reels(channel,title,sub,status,length_s,checks) VALUES(?,?,?,?,?,?)');
  [
    ['km','wait','Discipline is a decision you make once','Pick the workout time tonight, not tomorrow morning.',31,'oooo'],
    ['km','wait','Your bottle is a reminder, not an accessory','Fill it before you leave. Finish it before you sit.',29,'oooo'],
    ['wi','wait','What if you noticed everything?','Episode 4 · 7:12',432,'oooo'],
    ['hi','wait','The empire that ruled three seas','Османы · фильм v5 · 11:56',716,'oooo'],
  ].forEach(([c, s, t, sub, l, q]) => { const r = seed.run(c, t, sub, s, l, q); log(r.lastInsertRowid, 'system', 'seed', 'пример'); });
}

const TYPES = { '.mp4':'video/mp4', '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.css':'text/css', '.json':'application/json' };
const send = (res, code, body, type = 'application/json') => { res.writeHead(code, { 'Content-Type': type }); res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body)); };
const readBody = req => new Promise(ok => { let d = ''; req.on('data', c => d += c); req.on('end', () => ok(d ? JSON.parse(d) : {})); });

createServer(async (req, res) => {
  try {
    // Same-origin only: reject anything not addressed to our own host.
    if (!/^(127\.0\.0\.1|localhost)(:\d+)?$/.test(req.headers.host || '')) return send(res, 403, { error: 'host' });
    const url = new URL(req.url, 'http://x');
    if (url.pathname === '/api/reels' && req.method === 'GET')
      return send(res, 200, db.prepare('SELECT * FROM reels ORDER BY id').all());
    if (url.pathname === '/api/reels' && req.method === 'POST') {
      const b = await readBody(req);
      const r = db.prepare('INSERT INTO reels(channel,title,sub,status) VALUES(?,?,?,?)').run(b.channel, b.title, b.sub || '', 'draft');
      log(r.lastInsertRowid, 'owner', 'create', b.title);
      return send(res, 201, { id: r.lastInsertRowid });
    }
    const m = url.pathname.match(/^\/api\/reels\/(\d+)$/);
    if (m && req.method === 'PATCH') {
      const b = await readBody(req), id = +m[1];
      if (!STATUSES.has(b.status)) return send(res, 400, { error: 'status' });
      db.prepare('UPDATE reels SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?').run(b.status, id);
      log(id, 'owner', 'status', b.status);
      return send(res, 200, { ok: true });
    }
    const v = url.pathname.match(/^\/api\/reels\/(\d+)\/video$/);
    if (v) {
      const row = db.prepare('SELECT job_dir FROM reels WHERE id=?').get(+v[1]);
      const media = join(root, 'trials', 'reels', 'final');
      if (!row?.job_dir || !normalize(row.job_dir).startsWith(media)) return send(res, 404, { error: 'no video' });
      // Range support: the browser player needs it to seek and to show the first frame fast.
      const buf = await readFile(row.job_dir), range = req.headers.range?.match(/bytes=(\d*)-(\d*)/);
      if (!range) { res.writeHead(200, { 'Content-Type': 'video/mp4', 'Content-Length': buf.length, 'Accept-Ranges': 'bytes' }); return res.end(buf); }
      const start = range[1] ? +range[1] : 0, end = range[2] ? Math.min(+range[2], buf.length - 1) : buf.length - 1;
      res.writeHead(206, { 'Content-Type': 'video/mp4', 'Content-Range': `bytes ${start}-${end}/${buf.length}`, 'Content-Length': end - start + 1, 'Accept-Ranges': 'bytes' });
      return res.end(buf.subarray(start, end + 1));
    }
    const st = url.pathname.match(/^\/api\/settings\/(skills|custom|wardrobe)$/);
    if (st) {
      if (req.method === 'PUT') { const b = await readBody(req); db.prepare('INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)').run(st[1], JSON.stringify(b)); log(null, 'owner', st[1], JSON.stringify(b).slice(0, 200)); return send(res, 200, { ok: true }); }
      const s = db.prepare('SELECT value FROM settings WHERE key=?').get(st[1]);
      return send(res, 200, s ? JSON.parse(s.value) : (st[1] === 'skills' ? {} : []));
    }
    if (url.pathname === '/api/jobs') return send(res, 200, Object.fromEntries(jobs));
    const fxm = url.pathname.match(/^\/api\/reels\/(\d+)\/effects$/);
    if (fxm && req.method === 'POST') {
      const id = +fxm[1], b = await readBody(req);
      const row = db.prepare('SELECT * FROM reels WHERE id=?').get(id);
      if (!row?.job_dir) return send(res, 404, { error: 'no video' });
      if (jobs.get(id)?.state === 'running') return send(res, 409, { error: 'already running' });
      let okSet = FX_OK;
      try { okSet = new Set(JSON.parse(await readFile(join(root, 'app', 'fx-catalog.json'), 'utf8')).filter(c => c.status === 'ok' && !c.images && !DENY.has(c.id)).map(c => c.id)); } catch {}
      const list = (b.effects || []).filter(e => okSet.has(e.fx) && Number.isFinite(+e.start) && Number.isFinite(+e.end) && +e.end > +e.start && +e.end <= 120)
        .map(e => ({ fx: e.fx, start: +e.start, end: +e.end, ...(e.text ? { text: String(e.text).slice(0, 60) } : {}), ...(e.fx === 'moody' || e.fx === 'swipe' ? { grade: ['moody','bw','warm','cool','pop'].includes(e.grade) ? e.grade : 'warm' } : {}) }));
      if (!list.length) return send(res, 400, { error: 'no valid effects' });
      const base = row.base_path || row.job_dir, ts = Date.now();
      const plan = join(root, 'trials', 'reels', 'fx', `plan_${id}_${ts}.json`), raw = join(root, 'trials', 'reels', 'fx', `out_${id}_${ts}.mp4`);
      const out = join(root, 'trials', 'reels', 'final', `reel${id}_${ts}.mp4`);
      await writeFile(plan, JSON.stringify({ effects: list }));
      if (!row.base_path) db.prepare('UPDATE reels SET base_path=? WHERE id=?').run(base, id);
      jobs.set(id, { state: 'running', note: 'Эффекты накладываются', since: ts });
      const env = { ...process.env, PYTHONIOENCODING: 'utf-8' };
      const p1 = spawn(FX_PY, [FX_SCRIPT, '--plan', plan, base, raw], { env });
      p1.on('close', c1 => {
        if (c1 !== 0) { jobs.set(id, { state: 'error', note: 'Эффекты не наложились' }); return; }
        const p2 = spawn('ffmpeg', ['-v', 'error', '-y', '-i', raw, '-c:v', 'copy', '-af', 'loudnorm=I=-14:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', out]);
        p2.on('close', c2 => {
          if (c2 !== 0) { jobs.set(id, { state: 'error', note: 'Громкость не выровнялась' }); return; }
          db.prepare("UPDATE reels SET job_dir=?, status='wait', updated_at=CURRENT_TIMESTAMP WHERE id=?").run(out, id);
          log(id, 'owner', 'effects', list.map(e => e.fx).join(','));
          jobs.set(id, { state: 'done', note: 'Готово' });
        });
      });
      return send(res, 202, { started: true });
    }
    if (url.pathname === '/api/events')
    if (url.pathname === '/api/events') return send(res, 200, db.prepare('SELECT * FROM events ORDER BY id DESC LIMIT 100').all());
    // static files from app/
    const rel = url.pathname === '/' ? 'index.html' : normalize(url.pathname).replace(/^([\\/]|\.\.)+/, '');
    const file = join(root, 'app', rel);
    if (!file.startsWith(join(root, 'app'))) return send(res, 403, { error: 'path' });
    send(res, 200, await readFile(file), TYPES[extname(file)] || 'application/octet-stream');
  } catch (e) { send(res, e.code === 'ENOENT' ? 404 : 500, { error: String(e.message) }); }
}).listen(8791, '127.0.0.1', () => console.log('Content Studio: http://127.0.0.1:8791'));
