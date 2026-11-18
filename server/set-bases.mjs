// One-off: remember the effect-free source of each built reel, so effects can be re-applied from scratch.
import { DatabaseSync } from 'node:sqlite';
const db = new DatabaseSync('C:/src/content-studio/data/studio.db');
try { db.exec('ALTER TABLE reels ADD COLUMN base_path TEXT'); } catch {}
const fx = 'C:\\src\\content-studio\\trials\\reels\\fx\\';
const set = db.prepare('UPDATE reels SET base_path=? WHERE job_dir LIKE ?');
set.run(fx + 'km_missed_workout_en_nofx.mp4', '%km_missed_workout_en.mp4');
set.run(fx + 'km_plan_tonight_en_nofx.mp4', '%km_plan_tonight_en.mp4');
set.run(fx + 'km_boring_days_en_nofx.mp4', '%km_boring_days_en.mp4');
console.log(db.prepare('SELECT id,title,base_path FROM reels WHERE base_path IS NOT NULL').all());
