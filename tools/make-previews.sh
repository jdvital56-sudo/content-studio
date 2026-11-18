#!/bin/bash
# Renders a 4 s preview of each effect on a neutral stock clip (trial 18.11).
S=~/.claude/skills/effects; P=/c/src/content-studio/app/previews; D=/c/src/content-studio/trials/reels/fx
cd $D
run(){ n=$1; shift; PYTHONIOENCODING=utf-8 $S/.venv/Scripts/python.exe $S/scripts/fx.py "$@" --width 540 > prev_$n.log 2>&1 && echo "ok $n" || echo "FAIL $n"; }
run reject-stamp reject-stamp sample.mp4 $P/reject-stamp.mp4 --start 0.4 --end 3.5 --text "NOT MONDAY"
run tap tap sample.mp4 $P/tap.mp4 --start 0.3 --end 3.7 --opt at=2.0 --opt color=#C9AB7C
run countdown-flip countdown-flip sample.mp4 $P/countdown-flip.mp4 --start 0.3 --end 3.7
run moody moody sample.mp4 $P/moody.mp4 --start 0.3 --end 3.7 --opt grade=warm
run scribble scribble sample.mp4 $P/scribble.mp4 --start 0.3 --end 3.7 --text "DON'T SKIP"
run rabbit-hole rabbit-hole sample.mp4 $P/rabbit-hole.mp4 --start 0.8 --end 3.5
run dot-reveal dot-reveal sample.mp4 $P/dot-reveal.mp4 --start 0.0 --end 2.5
run headline-box headline-box sample.mp4 $P/headline-box.mp4 --start 0.3 --end 3.7 --text "REST DAY|IS PART OF THE PLAN"
echo done
