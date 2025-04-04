import os
import tempfile
import requests
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx

class TimelapseModel:
    @staticmethod
    def generate(video_urls, speed=2.5):
        temp_dir = tempfile.mkdtemp()
        clips = []

        for i, url in enumerate(video_urls):
            try:
                response = requests.get(url, stream=True, headers={
                    "User-Agent": "Mozilla/5.0"
                })
                if response.status_code != 200:
                    print(f"⚠️ Skipped (status {response.status_code}): {url}")
                    continue

                temp_path = os.path.join(temp_dir, f"clip_{i}.mp4")
                with open(temp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                size = os.path.getsize(temp_path)
                if size < 50 * 1024:
                    print(f"⚠️ Skipped small file ({size} bytes): {temp_path}")
                    continue

                print(f"✅ Downloaded: {temp_path} ({size} bytes)")

                # ✅ Speed up the clip
                clip = VideoFileClip(temp_path).fx(vfx.speedx, speed)
                clips.append(clip)

            except Exception as e:
                print(f"❌ Error loading {url}: {e}")
                continue

        if not clips:
            raise ValueError("No valid clips found to generate timelapse.")

        final = concatenate_videoclips(clips, method="compose")
        output_path = os.path.join(temp_dir, "timelapse.mp4")
        final.write_videofile(output_path, codec="libx264", audio=False)

        return output_path
