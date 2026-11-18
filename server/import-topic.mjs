// One-off recovery: import the best scripts of a finished topic run (final.json) as drafts, if the server was restarted before it could.
// node server/import-topic.mjs <topic folder> [channel]
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
const dir = process.argv[2], ch = process.argv[3] || 'km';
const db = new DatabaseSync('C:/src/content-studio/data/studio.db');
const f = JSON.parse(readFileSync(join(dir, 'final.json'), 'utf8'));
let n = 0;
for (const s of f.final || []) {
  if (db.prepare('SELECT 1 FROM reels WHERE title=? AND script IS NOT NULL').get(s.hook)) continue;
  const r = db.prepare('INSERT INTO reels(channel,title,sub,status,script) VALUES(?,?,?,?,?)').run(ch, s.hook, (s.spoken || '').slice(0, 110), 'draft', JSON.stringify(s));
  db.prepare('INSERT INTO events(reel_id,actor,action,note) VALUES(?,?,?,?)').run(r.lastInsertRowid, 'scriptwriter', 'script', s.hook_type || ''); n++;
}
console.log('imported', n, 'scripts');
