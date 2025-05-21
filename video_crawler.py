import os, time, requests
from datetime import datetime, timedelta, timezone
import pytz

BASE_URL = "https://www.bordertraffic.com/videoclips/free_california-baja_sanysidro-tijuana_passengerlines_0_255_"
SAVE_DIR = "data/videos"
pacific = pytz.timezone("America/Los_Angeles")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def download_video_at(dt):
    filename = dt.strftime("%Y_%m_%d_%H_%M") + ".mp4"
    url = f"{BASE_URL}{filename}"
    save_path = os.path.join(SAVE_DIR, filename)

    if os.path.exists(save_path):
        return

    try:
        r = requests.get(url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            ensure_dir(SAVE_DIR)
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            print(f"✅ Saved {filename}")
        else:
            print(f"❌ Not available: {url} [{r.status_code}]")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def download_latest():
    now = datetime.now(pacific)
    download_video_at(now)

def backfill_last_2_hours():
    now = datetime.now(pacific)
    for i in range(120):
        dt = now - timedelta(minutes=i)
        download_video_at(dt)

if __name__ == "__main__":
    ensure_dir(SAVE_DIR)
    if not any(f.endswith(".mp4") for f in os.listdir(SAVE_DIR)):
        print("📦 No existing videos found. Backfilling last 2 hours...")
        backfill_last_2_hours()
    while True:
        download_latest()
        time.sleep(29)