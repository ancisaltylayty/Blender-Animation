#!/usr/bin/env bash
# Render all six shot scripts (960 frames, 1080x1920, 64 samples), then assemble the short.
# Usage (from the project folder):  bash shots/render_all.sh
# Resumable: a beat whose folder already holds all its frames is skipped.
set -u
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-blender}"   # e.g.  BLENDER="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" bash shots/render_all.sh
LOG=renders/render_all.log
mkdir -p renders
echo "=== start $(date '+%F %T')" | tee -a "$LOG"
start=$(date +%s)
while read -r script beat count; do
  have=$(ls renders/$beat/f_*.png 2>/dev/null | wc -l)
  if [ "$have" -eq "$count" ]; then echo "$beat: already has $count frames, skipped" | tee -a "$LOG"; continue; fi
  t0=$(date +%s)
  "$BLENDER" -b --factory-startup --python "shots/$script.py" -- > "renders/$beat.render.log" 2>&1
  have=$(ls renders/$beat/f_*.png 2>/dev/null | wc -l)
  echo "$beat: $have/$count frames in $(( ($(date +%s)-t0)/60 )) min, $(grep -c Traceback renders/$beat.render.log) errors  [$(date '+%T')]" | tee -a "$LOG"
done <<EOF
shot1_reveal beat1 135
shot2_room beat2 90
shot3_branch beat3 195
shot4_stretch beat4 150
shot5_space beat5 210
shot6_loop beat6 180
EOF
echo "render total $(( ($(date +%s)-start)/60 )) min" | tee -a "$LOG"
python shots/assemble.py --words words_placeholder.json --out renders/pembuluh_darah.mp4 >> "$LOG" 2>&1 \
  && echo "assembled renders/pembuluh_darah.mp4" | tee -a "$LOG" \
  || echo "assemble FAILED, see $LOG" | tee -a "$LOG"
echo "=== end $(date '+%F %T')" | tee -a "$LOG"
