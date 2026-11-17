// Content Studio: local server. Listens on 127.0.0.1 only (see CLAUDE.md).
// Serves the wall (app/) and a small JSON API over SQLite (node:sqlite, built into Node).
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
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
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reel_id INTEGER, actor TEXT, action TEXT, note TEXT,
  at TEXT DEFAULT CURRENT_TIMESTAMP
);`);

const STATUSES = new Set(['draft','render','check','wait','ok','pub','bad']);
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

const TYPES = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.css':'text/css', '.json':'application/json' };
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
    if (url.pathname === '/api/events') return send(res, 200, db.prepare('SELECT * FROM events ORDER BY id DESC LIMIT 100').all());
    // static files from app/
    const rel = url.pathname === '/' ? 'index.html' : normalize(url.pathname).replace(/^([\\/]|\.\.)+/, '');
    const file = join(root, 'app', rel);
    if (!file.startsWith(join(root, 'app'))) return send(res, 403, { error: 'path' });
    send(res, 200, await readFile(file), TYPES[extname(file)] || 'application/octet-stream');
  } catch (e) { send(res, e.code === 'ENOENT' ? 404 : 500, { error: String(e.message) }); }
}).listen(8791, '127.0.0.1', () => console.log('Content Studio: http://127.0.0.1:8791'));
