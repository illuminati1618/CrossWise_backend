#!/bin/bash

# Directory to store downloaded clips
DEST_DIR="/home/ubuntu/CrossWiseVids"
mkdir -p "$DEST_DIR"

# Base URL
BASE_URL="https://www.bordertraffic.com/videoclips/free_california-baja_sanysidro-tijuana_passengerlines_0_255"

# Get current time
NOW=$(date +"%s")

# If less than 3 videos exist, scan past 3 hours (180 minutes)
EXISTING_COUNT=$(ls "$DEST_DIR"/*.mp4 2>/dev/null | wc -l)

if [ "$EXISTING_COUNT" -lt 3 ]; then
  SCAN_RANGE=180
else
  SCAN_RANGE=10
fi

# Function to pad numbers
pad() {
  printf "%02d" "$1"
}

# Loop through SCAN_RANGE minutes back from now
for ((i=0; i<=SCAN_RANGE; i++)); do
  TARGET_TIME=$((NOW - i * 60))
  YEAR=$(date -d @$TARGET_TIME +"%Y")
  MONTH=$(pad $(date -d @$TARGET_TIME +"%-m"))
  DAY=$(pad $(date -d @$TARGET_TIME +"%-d"))
  HOUR=$(pad $(date -d @$TARGET_TIME +"%-H"))
  MINUTE=$(pad $(date -d @$TARGET_TIME +"%-M"))

  TIME_CODE="${HOUR}_${MINUTE}"
  FILENAME="${YEAR}_${MONTH}_${DAY}_${TIME_CODE}.mp4"
  URL="${BASE_URL}_${FILENAME}"
  OUTPUT_PATH="$DEST_DIR/$FILENAME"

  # Skip if file already exists
  if [ -f "$OUTPUT_PATH" ]; then
    continue
  fi

  # Try downloading
  curl -s -f -A "Mozilla/5.0" "$URL" -o "$OUTPUT_PATH.tmp"

  # Check if file is large enough
  if [ -s "$OUTPUT_PATH.tmp" ] && [ $(stat -c%s "$OUTPUT_PATH.tmp") -ge 50000 ]; then
    mv "$OUTPUT_PATH.tmp" "$OUTPUT_PATH"
    echo "✅ Saved: $FILENAME"
  else
    rm -f "$OUTPUT_PATH.tmp"
  fi

done

# Cleanup: only keep the most recent 1008 files (7 days if 1 file every 10 mins)
ls -1t "$DEST_DIR"/*.mp4 2>/dev/null | tail -n +1009 | xargs -r rm -f