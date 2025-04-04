#!/bin/bash

SAVE_DIR="/home/ubuntu/CrossWiseVids"
BASE_URL="https://www.bordertraffic.com/videoclips/free_california-baja_sanysidro-tijuana_passengerlines_0_255"

mkdir -p "$SAVE_DIR"

pad() {
    printf "%02d" "$1"
}

download_video() {
    local datetime=$1
    local filename="${datetime}.mp4"
    local url="${BASE_URL}_${datetime}.mp4"
    local path="$SAVE_DIR/$filename"

    if [ ! -f "$path" ]; then
        echo "[INFO] Trying: $filename"
        curl -f -s -A "Mozilla/5.0" "$url" -o "$path"
        if [ $? -eq 0 ]; then
            echo "[✅] Downloaded: $filename"
        else
            echo "[⚠️] Not available: $filename"
            rm -f "$path"
        fi
    else
        echo "[ℹ️] Already exists: $filename"
    fi
}

cd "$SAVE_DIR"
TOTAL_FILES=$(ls -1 *.mp4 2>/dev/null | wc -l)

if [ "$TOTAL_FILES" -lt 3 ]; then
    echo "[🔄] Less than 3 files found. Scanning past 3 hours..."

    for i in $(seq 180 -10 0); do
        dt=$(date -u -d "$i minutes ago" +"%Y_%m_%d_%H_%M")
        min_rounded=$(pad $((10 * ($(echo $dt | cut -d'_' -f5) / 10))))
        prefix=$(echo $dt | cut -d'_' -f1-4)
        rounded_dt="${prefix}_${min_rounded}"
        download_video "$rounded_dt"
    done
else
    echo "[🕒] Folder has $TOTAL_FILES videos. Checking current 10-min slot..."
    dt=$(date -u +"%Y_%m_%d_%H")
    min=$(date -u +"%M")
    min_rounded=$(pad $((10 * (min / 10))))
    download_video "${dt}_${min_rounded}"
fi

# Prune to latest 1008 files (1 week)
MAX_FILES=1008
TOTAL=$(ls -1 *.mp4 2>/dev/null | wc -l)
if [ "$TOTAL" -gt "$MAX_FILES" ]; then
    TO_DELETE=$((TOTAL - MAX_FILES))
    echo "[🧹] Cleaning $TO_DELETE old file(s)..."
    ls -1t *.mp4 | tail -n "$TO_DELETE" | xargs rm -f
fi
