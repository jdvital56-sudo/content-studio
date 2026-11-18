#!/bin/bash
# Scriptwriter v2 -> Critic. Passport + research + hook formulas in, scored scripts out. Uses `claude -p` (subscription).
# usage: bash tools/write-scripts-v2.sh <channel passport> <research file> <outdir> [count]
P="$1"; R="$2"; O="$3"; N="${4:-14}"; T="$5"; S="$6"; F="${7:-mix}"; L="$8"   # T topic, S style rules, F format mix|text|tania|stock, L owner's footage descriptions
mkdir -p "$O"
# plain variables: special characters inside ${x:+...} break the heredoc in this bash
TL=""; [ -n "$T" ] && TL="Topic focus - every script must be about this: $T"
SL=""; [ -n "$S" ] && SL="Owner script style rules - follow them, they override your defaults: $S"
# Formats. "text" follows the owner's reference reels (18.11): no voice-over, a real person training on camera, 3-5 typed lines, a question at the end.
FT="FORMAT text: NO voice-over. Write 3 to 5 on-screen text beats for a real workout clip, each beat 1 to 3 short lines (max 6 words per line). Beat 1 is a callout hook to a narrow audience plus a pain (example pattern: Women over 30: / are you STILL / rushing your reps?). The last beat is a question that invites comments or a save. Put the beats in the field beats as a list of lists of strings, and put all beat lines joined with spaces into spoken. The text must describe exactly what the person does in the footage below; never name an exercise that is not in it. Put the file name of the footage you wrote for into the field footage. Available footage: ${L:-none uploaded}."
FV="FORMAT tania: voice-over spoken by the host Tania (cartoon) with effects, max 45 words, as described below."
FS="FORMAT stock: voice-over over stock footage and graphics, the host is not shown, max 45 words."
case "$F" in text) FL="$FT Every script uses FORMAT text.";; tania) FL="$FV Every script uses FORMAT tania.";; stock) FL="$FS Every script uses FORMAT stock.";; *) FL="Mix the formats: about half FORMAT text, a quarter FORMAT tania, a quarter FORMAT stock. $FT $FV $FS";; esac
{
cat "$P"; echo; echo "=== RESEARCH ==="; cat "$R"; echo
cat <<EOF
=== TASK (Scriptwriter) ===
$TL
$SL
$FL
Each item must have a field "format" with the value text, tania or stock.
Current channel goal: grow followers. Do NOT advertise products and do NOT use product keywords for direct messages. The call to action is follow, save or share.
You are the head scriptwriter of a short-video factory. Write $N DIFFERENT candidate reel scripts for this channel in English.
Rules:
- Each script is 25-32 seconds spoken, at most 45 words in SPOKEN. 1.75 words per second.
- HOOK: the first line, at most 8 words, must stop the scroll AND be readable without sound. Use a different formula from the research list for each script (number+deadline, myth, pain-then-relief, mistake, anti-hook, open loop, direct address with action, concrete object). Never start with "Hey", a greeting, or a question everyone has heard.
- Structure: HOOK -> open loop or tension -> ONE concrete micro-step (a number, a time, an object, a place) -> short payoff line -> CTA (Follow for ..., Save this, or Send this to a friend). The brand slogan only in at most 3 of the scripts.
- Be specific and slightly surprising. No generic motivation lines like "stay consistent" or "believe in yourself".
- Follow every rule and ban in the passport (no body-shame, no before/after, no weight-loss promises, no invented numbers, no "Pixar", no aviation).
- A claim about health must be safe and general; add nothing the nutritionist would not sign.
- Also give per script: caption lines for the screen (max 7, each max 5 words), the stock-footage search idea for each line, and which Tania pose emotion fits each line (joy, serious, doubt, surprise, thoughtful).
Output ONLY a JSON array, no prose. Each item: {"id":1,"hook_type":"...","hook":"...","spoken":"...","captions":["..."],"cta":"FOLLOW|SAVE|SHARE","visuals":["..."],"tania":["..."],"why":"one sentence why this stops the scroll"}.
EOF
} > "$O/writer-prompt.txt"
claude -p --output-format json --tools "" < "$O/writer-prompt.txt" > "$O/writer.json" 2> "$O/writer.err"
python - "$O" <<'PY'
import json,sys,re
o=sys.argv[1]; d=json.load(open(o+'/writer.json',encoding='utf-8')); r=d.get('result','')
m=re.search(r'\[.*\]',r,re.S); open(o+'/candidates.json','w',encoding='utf-8').write(m.group(0) if m else r)
print('writer cost',d.get('total_cost_usd'),'candidates',len(json.loads(m.group(0))) if m else 0)
PY
{
cat "$P"; echo; echo "=== CANDIDATES ==="; cat "$O/candidates.json"; echo
cat <<EOF
=== TASK (Critic) ===
You are a ruthless short-video critic. Score every candidate 0-10 on: hook_strength (stops the scroll in 2 s and readable on mute), specificity (concrete number/object/time, not generic), novelty (not what every fitness account says), payoff (viewer gets one clear thing), passport_safety (10 = no ban violated, 0 = violates). Compute total = hook*2 + specificity + novelty + payoff + safety (max 60). Reject any with safety below 8.
Then for the 6 best, REWRITE the weakest line so each reaches at least 9 on hook_strength, and keep spoken text at most 45 words.
Output ONLY a JSON object: {"scores":[{"id":1,"hook":x,"specificity":x,"novelty":x,"payoff":x,"safety":x,"total":x,"verdict":"keep|rewrite|drop","note":"..."}],"final":[<the 6 best scripts, same fields as candidates, with improvements and the same visuals/tania lists>]}.
EOF
} > "$O/critic-prompt.txt"
claude -p --output-format json --tools "" < "$O/critic-prompt.txt" > "$O/critic.json" 2> "$O/critic.err"
python - "$O" <<'PY'
import json,sys,re
o=sys.argv[1]; d=json.load(open(o+'/critic.json',encoding='utf-8')); r=d.get('result','')
m=re.search(r'\{.*\}',r,re.S); open(o+'/final.json','w',encoding='utf-8').write(m.group(0) if m else r)
print('critic cost',d.get('total_cost_usd'))
PY
echo done
