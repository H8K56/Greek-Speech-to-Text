import json
import re
from pathlib import Path

def srt_time_to_seconds(time_str):
    """Converts SRT time string (HH:MM:SS,ms) to total seconds."""
    try:
        parts = time_str.replace(',', '.').split(':')
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError) as e:
        print(f"❌ Error converting time string '{time_str}': {e}")
        return None

def load_dictionary(dict_path):
    """
    Load the dictionary and organize it for efficient lookup.
    Returns a tuple: (multi_word_phrases_by_length, sorted_phrase_lengths, single_word_map).
    - multi_word_phrases_by_length: {length: {greek_phrase.lower(): cypriot_phrase}}
    - sorted_phrase_lengths: List of phrase lengths sorted in descending order.
    - single_word_map: {greek_word.lower(): cypriot_word}
    """
    with open(dict_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    single_word_map = {}
    multi_word_phrases_by_length = {}

    for entry in data:
        greek_word = entry["greek_word"].lower()
        num_words = len(greek_word.split())

        if num_words == 1:
            single_word_map[greek_word] = entry["cypriot_word"]
        else:
            if num_words not in multi_word_phrases_by_length:
                multi_word_phrases_by_length[num_words] = {}
            multi_word_phrases_by_length[num_words][greek_word] = entry["cypriot_word"]

    sorted_phrase_lengths = sorted(multi_word_phrases_by_length.keys(), reverse=True)
    return multi_word_phrases_by_length, sorted_phrase_lengths, single_word_map

def tokenize_text(text):
    """
    Tokenizes Greek text into words and punctuation, preserving original capitalization.
    Handles apostrophes within words and keeps punctuation as separate tokens.
    """
    return re.findall(r"\b\w+'?\w*\b|[^\w\s]", text, re.UNICODE)

def convert_tokens_to_cypriot(full_text_tokens, dictionary_data):
    """
    Converts a flattened list of tokens to Cypriot Greek using the dictionary.
    Prioritizes multi-word phrase matches and handles capitalization.
    """
    multi_word_phrases_by_length, sorted_phrase_lengths, single_word_map = dictionary_data
    
    converted_tokens = []
    i = 0
    while i < len(full_text_tokens):
        current_token = full_text_tokens[i]
        lower_current_token = current_token.lower()
        matched = False

        # Try to match multi-word phrases (longest first)
        for length in sorted_phrase_lengths:
            if i + length <= len(full_text_tokens):
                phrase_to_check = " ".join(full_text_tokens[i : i + length]).lower()
                
                if phrase_to_check in multi_word_phrases_by_length.get(length, {}):
                    replacement = multi_word_phrases_by_length[length][phrase_to_check]
                    
                    if replacement is not None and full_text_tokens[i][0].isupper():
                        replacement = replacement.capitalize()
                    
                    if replacement is not None:
                        converted_tokens.append(replacement)
                    
                    i += length
                    matched = True
                    break

        if matched:
            continue

        # If no multi-word phrase matched, try single-word lookup
        if lower_current_token in single_word_map:
            replacement = single_word_map[lower_current_token]
            if replacement is not None and current_token[0].isupper():
                replacement = replacement.capitalize()
            if replacement is not None:
                converted_tokens.append(replacement)
            else: # Fallback if replacement became None for some reason (shouldn't happen if dict clean)
                converted_tokens.append(current_token)
        else:
            # If no match, keep the original token
            converted_tokens.append(current_token)
        i += 1

    return converted_tokens # Return a list of converted tokens

def parse_srt(srt_path):
    """Parses an SRT file into a list of dictionaries, preserving original index."""
    entries = []
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = re.split(r'\n\s*\n', content.strip())

        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) < 3:
                continue

            time_match = re.match(r"(\d{2}:\d{2}:\d{2}[,.]\d{3}) --> (\d{2}:\d{2}:\d{2}[,.]\d{3})", lines[1])
            if not time_match:
                print(f"⚠️ Warning: Malformed timecode in {srt_path} block: '{lines[1]}'. Skipping block.")
                continue

            start_time_str, end_time_str = time_match.groups()
            start_seconds = srt_time_to_seconds(start_time_str)
            end_seconds = srt_time_to_seconds(end_time_str)

            if start_seconds is None or end_seconds is None:
                continue

            text = " ".join(lines[2:]).strip()
            # Clean up unwanted elements from subtitles (HTML tags, brackets, parentheses)
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\[(.*?)\]', '', text)
            text = re.sub(r'\((.*?)\)', '', text)
            text = re.sub(r'[^\u0370-\u03FF\u1F00-\u1FFF\s]', '', text) # Keep only Greek and spaces
            text = re.sub(r'\s+', ' ', text).strip()

            if not text:
                continue

            entries.append({
                "index": int(lines[0]),
                "start": start_seconds,
                "end": end_seconds,
                "text": text
            })
    except FileNotFoundError:
        print(f"❌ Error: SRT file not found at: {srt_path}")
    except Exception as e:
        print(f"❌ An unexpected error occurred while parsing SRT file {srt_path}: {e}")
    return entries

def batch_convert(srt_folder, audio_folder, dict_path, output_combined=None):
    """
    Converts SRT subtitles to Cypriot Greek and combines with audio info into a JSONL file.
    Handles phrases spanning across multiple SRT segments.
    """
    try:
        dictionary_data = load_dictionary(dict_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"❌ Failed to load dictionary from '{dict_path}': {e}")
        return

    srt_folder_path = Path(srt_folder)
    audio_folder_path = Path(audio_folder)

    if not srt_folder_path.is_dir():
        print(f"❌ Error: SRT folder not found or is not a directory: {srt_folder_path}")
        return
    if not audio_folder_path.is_dir():
        print(f"❌ Error: Audio folder not found or is not a directory: {audio_folder_path}")
        return

    audio_exts = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
    audio_files = {f.stem: f for f in audio_folder_path.iterdir() if f.suffix.lower() in audio_exts}
    srt_files = {f.stem: f for f in srt_folder_path.iterdir() if f.suffix.lower() == '.srt'}

    combined_entries = []

    for stem, srt_file in srt_files.items():
        audio_file = audio_files.get(stem)

        if audio_file and audio_file.exists():
            print(f"📁 Processing: Audio '{audio_file.name}' and SRT '{srt_file.name}'")
            original_segments = parse_srt(srt_file)

            if not original_segments:
                print(f"⚠️ No valid segments found in SRT file: {srt_file.name}")
                continue

            # Flatten all original tokens with their segment index
            all_tokens_with_indices = []
            for idx, seg in enumerate(original_segments):
                tokens = tokenize_text(seg["text"])
                for t in tokens:
                    all_tokens_with_indices.append((idx, t))
            
            # This list will store the converted text for each original segment index
            # It's initialized with empty strings for proper appending later
            final_converted_segments_texts = [[] for _ in range(len(original_segments))]
            
            current_global_token_idx = 0
            while current_global_token_idx < len(all_tokens_with_indices):
                matched_phrase_len = 0
                matched_cypriot_word = None
                
                # Try longest multi-word phrase match spanning across segments
                for length in dictionary_data[1]: # sorted_phrase_lengths (descending)
                    if current_global_token_idx + length <= len(all_tokens_with_indices):
                        potential_phrase_tokens = [
                            all_tokens_with_indices[k][1] # Get just the token text
                            for k in range(current_global_token_idx, current_global_token_idx + length)
                        ]
                        phrase_str = " ".join(potential_phrase_tokens).lower()
                        
                        if phrase_str in dictionary_data[0].get(length, {}): # multi_word_phrases_by_length[length]
                            matched_cypriot_word = dictionary_data[0][length][phrase_str]
                            matched_phrase_len = length
                            break # Found the longest match, exit inner loop

                if matched_phrase_len > 0 and matched_cypriot_word is not None:
                    # A multi-word phrase was matched
                    first_original_token_in_phrase = all_tokens_with_indices[current_global_token_idx][1]
                    if first_original_token_in_phrase[0].isupper():
                        matched_cypriot_word = matched_cypriot_word.capitalize()
                    
                    # Add the converted phrase to the list of tokens for the first segment it spans
                    first_original_segment_idx = all_tokens_with_indices[current_global_token_idx][0]
                    final_converted_segments_texts[first_original_segment_idx].append(matched_cypriot_word)
                    
                    # Advance the global token index by the length of the matched phrase
                    current_global_token_idx += matched_phrase_len
                else:
                    # No multi-word phrase match, try single word
                    current_token_info = all_tokens_with_indices[current_global_token_idx]
                    original_seg_idx = current_token_info[0]
                    original_token = current_token_info[1]
                    lower_original_token = original_token.lower()

                    converted_single_word = original_token # Default to original

                    if lower_original_token in dictionary_data[2]: # single_word_map
                        temp_word = dictionary_data[2][lower_original_token]
                        if temp_word is not None:
                            converted_single_word = temp_word
                            if original_token[0].isupper():
                                converted_single_word = converted_single_word.capitalize()
                    
                    # Add the converted single word to the list of tokens for its original segment
                    final_converted_segments_texts[original_seg_idx].append(converted_single_word)
                    
                    current_global_token_idx += 1 # Advance by one token

            # Now, construct the combined_entries from the re-assembled segment texts
            for idx, original_seg in enumerate(original_segments):
                # Join the list of converted tokens for each segment into a single string
                converted_text = " ".join(final_converted_segments_texts[idx]).strip()
                
                if not converted_text: # Skip segments that became empty after conversion (e.g., consumed by a multi-segment phrase)
                    continue
                
                combined_entries.append({
                    "audio_filepath": str(audio_file.resolve()),
                    "start": original_seg["start"],
                    "end": original_seg["end"],
                    "text": converted_text
                })
        else:
            print(f"⚠️ No matching audio file found for SRT: '{srt_file.name}'. Skipping.")

    if combined_entries:
        if output_combined:
            try:
                with open(output_combined, "w", encoding="utf-8") as f:
                    for entry in combined_entries:
                        json.dump(entry, f, ensure_ascii=False)
                        f.write("\n")
                print(f"✅ Combined dataset written to: '{output_combined}' with {len(combined_entries)} entries.")
            except IOError as e:
                print(f"❌ Error writing combined dataset to '{output_combined}': {e}")
        else:
            print("ℹ️ Successfully processed segments. No file output path given.")
    else:
        print("🤷 No valid audio-SRT pairs found or processed. No output file generated.")

if __name__ == "__main__":
    srt_folder = "srt_files"
    audio_folder = "converted_wav"
    dict_path = "cylingo_lexicon.json"
    output_combined = "output_data.jsonl"

    batch_convert(srt_folder, audio_folder, dict_path, output_combined)