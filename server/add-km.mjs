// One-off: register the KM Editorial versions of the three trial reels (cartoon Tania, paper + gold).
import { DatabaseSync } from 'node:sqlite';
import { join } from 'node:path';
const db = new DatabaseSync('C:/src/content-studio/data/studio.db');
const dir = join('C:/src/content-studio', 'trials', 'reels', 'final');
const rows = [
  ['Missed a workout?', 'KM Editorial · Таня · DM SOCKS', 16, 'km_missed_workout_en_KMED'],
  ['Motivation is not coming today', 'KM Editorial · Таня · DM PEN', 14, 'km_plan_tonight_en_KMED'],
  ['Nobody sees the boring days', 'KM Editorial · Таня · DM BOTTLE', 17, 'km_boring_days_en_KMED'],
];
for (const [t, s, l, f] of rows) {
  const p = join(dir, f + '.mp4');
  if (db.prepare('SELECT 1 FROM reels WHERE job_dir=?').get(p)) continue;
  const r = db.prepare('INSERT INTO reels(channel,title,sub,status,length_s,checks,job_dir) VALUES(?,?,?,?,?,?,?)').run('km', t, s, 'wait', l, 'oooo', p);
  db.prepare('INSERT INTO events(reel_id,actor,action,note) VALUES(?,?,?,?)').run(r.lastInsertRowid, 'km_editorial', 'built', 'KM Editorial + мультяшная Таня');
}
db.prepare("UPDATE reels SET sub = 'Вариант Б: сток · ' || sub WHERE base_path IS NOT NULL AND sub NOT LIKE 'Вариант Б%'").run();
console.log(db.prepare('SELECT id,sub FROM reels WHERE job_dir IS NOT NULL').all().map(x => x.id + ' ' + x.sub));
