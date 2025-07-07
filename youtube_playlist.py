import os
import subprocess
import yt_dlp
import pysrt
import json
from glob import glob

def download_playlist(playlist_url, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'yesplaylist': True,
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
        result = ydl.extract_info(playlist_url, download=True)
        if result is not None:
            if isinstance(result, dict) and 'entries' in result and result['entries'] is not None:
                video_ids = [entry['id'] for entry in result['entries'] if entry and 'id' in entry]
            elif isinstance(result, dict) and 'id' in result:
                video_ids = [result['id']]
            else:
                video_ids = []
        else:
            video_ids = []

    print(f"Downloaded {len(video_ids)} videos.")
    return video_ids

def srt_to_manifest(srt_path, audio_path, manifest_path):
    try:
        subs = pysrt.open(srt_path)
    except:
        print(f"[!] Failed to read subtitles: {srt_path}")
        return

    with open(manifest_path, 'a', encoding='utf-8') as f:
        for sub in subs:
            entry = {
                "audio_filepath": audio_path,
                "start_time": sub.start.to_time().strftime('%H:%M:%S.%f')[:-3],
                "end_time": sub.end.to_time().strftime('%H:%M:%S.%f')[:-3],
                "text": sub.text.replace('\n', ' ')
            }
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

def process_playlist(playlist_url, output_dir="downloads"):
    manifest_path = os.path.join(output_dir, 'manifest.jsonl')
    if os.path.exists(manifest_path):
        os.remove(manifest_path)

    video_ids = download_playlist(playlist_url, output_dir=output_dir)

    for vid in video_ids:
        srt_file = os.path.join(output_dir, f"{vid}.el.srt")
        audio_file = os.path.join(output_dir, f"{vid}.mp3")
        if os.path.exists(srt_file) and os.path.exists(audio_file):
            srt_to_manifest(srt_file, audio_file, manifest_path)
        else:
            print(f"[!] Missing files for {vid}: skipping")

    print(f"Final manifest at: {manifest_path}")


playlist_url = "https://youtube.com/playlist?list=PLspmRduqmP9WLKQiWEFma9KdqFNyZcSj1&si=BU0QPmWQlbC3PWlh"
process_playlist(playlist_url)
