import os
import subprocess

input_dir = "downloads"
output_dir = "converted_wav"
os.makedirs(output_dir, exist_ok=True)

# Section 1: Convert all audio files in the input directory
# for filename in os.listdir(input_dir):
#     if filename.endswith(".mpga") or filename.endswith(".mp3") or filename.endswith(".m4a"):
#         input_path = os.path.join(input_dir, filename)
#         output_filename = os.path.splitext(filename)[0] + ".wav"
#         output_path = os.path.join(output_dir, output_filename)

#         subprocess.run([
#             "ffmpeg", "-i", input_path,
#             "-ac", "1", "-ar", "16000",
#             "-c:a", "pcm_s16le",
#             output_path
#         ])

# Section 2: Convert only specific files (uncomment and edit the list below)
specific_files = ["ktvQVf7mQs8.mp3","SwAl8mYs_ZU.mp3","FXGlAHbXWJ0.mp3","Om5qWcbwBFA.mp3","_v65uDbQTvg.mp3"]
for filename in specific_files:
    input_path = os.path.join(input_dir, filename)
    output_filename = os.path.splitext(filename)[0] + ".wav"
    output_path = os.path.join(output_dir, output_filename)

    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le",
        output_path
    ])
