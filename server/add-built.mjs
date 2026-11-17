// One-off: register reels built by reel-factory (trial 18.11) on the wall.
import { DatabaseSync } from 'node:sqlite';
import { join } from 'node:path';
const root = 'C:/src/content-studio';
const db = new DatabaseSync(join(root, 'data', 'studio.db'));
const final = join(root, 'trials', 'reels', 'final');
const rows = [
  ['Missed a workout?', 'Restart today · DM SOCKS', 16, 'km_missed_workout_en'],
  ['Motivation is not coming today', 'Write it by hand · DM PEN', 14, 'km_plan_tonight_en'],
  ['Nobody sees the boring days', 'Show up anyway · DM BOTTLE', 17, 'km_boring_days_en'],
];
const ins = db.prepare('INSERT INTO reels(channel,title,sub,status,length_s,checks,job_dir) VALUES(?,?,?,?,?,?,?)');
for (const [t, s, l, f] of rows) {
  const path = join(final, f + '.mp4');
  if (db.prepare('SELECT 1 FROM reels WHERE job_dir=?').get(path)) continue;
  const r = ins.run('km', t, s, 'wait', l, 'oono', path);
  db.prepare('INSERT INTO events(reel_id,actor,action,note) VALUES(?,?,?,?)').run(r.lastInsertRowid, 'reel-factory', 'built', 'настоящий ролик');
}
console.log(db.prepare('SELECT id,title,job_dir FROM reels WHERE job_dir IS NOT NULL').all());
