// One-off: register the second batch (follower-growth scripts, cartoon Tania poses, no product ads).
import { DatabaseSync } from 'node:sqlite';
import { join } from 'node:path';
const db = new DatabaseSync('C:/src/content-studio/data/studio.db');
const dir = join('C:/src/content-studio', 'trials', 'reels', 'final');
const rows = [
  ["Don't go to the gym tomorrow", 'KM Editorial · Таня · призыв Follow', 19, 'km_gym_tomorrow_en_V2'],
  ['Skipped training? Ten p.m. fixes it', 'KM Editorial · Таня · призыв Follow', 19, 'km_ten_pm_en_V2'],
  ['Phone down. Stand up. Right now.', 'KM Editorial · Таня · призыв Save', 18, 'km_phone_down_en_V2'],
];
for (const [t, s, l, f] of rows) {
  const p = join(dir, f + '.mp4');
  if (db.prepare('SELECT 1 FROM reels WHERE job_dir=?').get(p)) continue;
  const r = db.prepare('INSERT INTO reels(channel,title,sub,status,length_s,checks,job_dir) VALUES(?,?,?,?,?,?,?)').run('km', t, s, 'wait', l, 'oooo', p);
  db.prepare('INSERT INTO events(reel_id,actor,action,note) VALUES(?,?,?,?)').run(r.lastInsertRowid, 'km_editorial_v2', 'built', 'позы Тани, рот по голосу, сток, эффекты');
}
console.log(db.prepare('SELECT id,title FROM reels WHERE job_dir IS NOT NULL ORDER BY id').all().map(x => x.id + ' ' + x.title));
