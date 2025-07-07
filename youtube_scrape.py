import os
import subprocess
import yt_dlp
import pysrt
import json

def download_youtube_audio_and_subs(url, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['el'],
        'subtitlesformat': 'srt',
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id") # type: ignore
        srt_path = os.path.join(output_dir, f"{video_id}.el.srt")
        mp3_path = os.path.join(output_dir, f"{video_id}.mp3")
        return srt_path, mp3_path

def srt_to_manifest(srt_path, audio_path, manifest_path):
    subs = pysrt.open(srt_path)
    manifest = []

    for sub in subs:
        entry = {
            "audio_filepath": audio_path,
            "start_time": sub.start.to_time().strftime('%H:%M:%S.%f')[:-3],
            "end_time": sub.end.to_time().strftime('%H:%M:%S.%f')[:-3],
            "text": sub.text.replace('\n', ' ')
        }
        manifest.append(entry)

    with open(manifest_path, 'w', encoding='utf-8') as f:
        for entry in manifest:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

    print(f"Manifest saved to {manifest_path}")


url = "https://www.youtube.com/watch?v=7M4DQHf1J2A"
srt_path, mp3_path = download_youtube_audio_and_subs(url)
manifest_path = mp3_path.replace('.mp3', '.jsonl')
srt_to_manifest(srt_path, mp3_path, manifest_path)
