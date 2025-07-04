import streamlit as st
import os
import tempfile
import uuid
import subprocess
from yt_dlp import YoutubeDL
import time

# ------------------ Page Setup ------------------
st.set_page_config(page_title="YT Clipper", layout="centered")

# ------------------ Mobile-Friendly CSS + PWA ------------------
st.markdown("""
    <head>
      <meta name="mobile-web-app-capable" content="yes">
      <meta name="apple-mobile-web-app-capable" content="yes">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="manifest" href="manifest.json">
      <style>
        video, iframe {
          max-width: 100% !important;
          height: auto !important;
          border-radius: 12px;
          box-shadow: 0 0 8px rgba(0,0,0,0.2);
        }
        .block-container {
          padding: 1rem;
        }
      </style>
    </head>
""", unsafe_allow_html=True)

# ------------------ UI ------------------
st.title("🎬 Mobile YouTube Clipper")

video_url = st.text_input("Paste YouTube video URL")
if video_url:
    st.markdown("### Preview:")
    st.video(video_url)

col1, col2 = st.columns(2)
with col1:
    start_min = st.number_input("Start Minute", min_value=0, value=0)
    start_sec = st.number_input("Start Second", min_value=0, max_value=59, value=0)
with col2:
    end_min = st.number_input("End Minute", min_value=0, value=0)
    end_sec = st.number_input("End Second", min_value=1, max_value=59, value=10)

quality = st.selectbox("Download Quality", ["720p", "1080p", "1440p"])

if st.button("🎞️ Create Clip"):
    if not video_url:
        st.error("Please enter a video URL")
        st.stop()

    start_time = start_min * 60 + start_sec
    end_time = end_min * 60 + end_sec
    duration = end_time - start_time
    if duration <= 0:
        st.error("End time must be after start time.")
        st.stop()

    with st.spinner("Downloading and clipping..."):
        tempdir = tempfile.TemporaryDirectory()
        uid = str(uuid.uuid4())[:8]
        raw_path = os.path.join(tempdir.name, f"video_{uid}.mp4")
        clip_path = os.path.join(tempdir.name, f"clip_{uid}.mp4")

        # Download YouTube video
        ydl_opts = {
            'format': f'bestvideo[height<={quality.replace("p","")}]+bestaudio/best',
            'outtmpl': raw_path,
            'quiet': True,
            'merge_output_format': 'mp4'
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            st.error(f"Download failed: {e}")
            st.stop()

        # Progress bar simulation (FFmpeg doesn't give real-time progress easily)
        progress_text = st.empty()
        progress_bar = st.progress(0)
        progress_text.text("Clipping video...")

        for i in range(0, 80, 8):
            progress_bar.progress(i / 100)
            time.sleep(0.15)

        # Run FFmpeg
        clip_cmd = [
            "ffmpeg", "-ss", str(start_time), "-t", str(duration), "-i", raw_path,
            "-c:v", "copy", "-c:a", "copy", clip_path, "-y"
        ]

        try:
            subprocess.run(clip_cmd, check=True)
        except subprocess.CalledProcessError as e:
            st.error(f"Failed to create clip: {e}")
            st.stop()

        progress_bar.progress(1.0)
        progress_text.text("✅ Done!")

        # Show + download final
        st.success("Clip created successfully!")
        st.video(clip_path)
        with open(clip_path, "rb") as f:
            st.download_button("📥 Download Clip", f, file_name="short_clip.mp4", mime="video/mp4")

        tempdir.cleanup()
