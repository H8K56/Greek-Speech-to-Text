import re
import json

def load_dictionary(dict_path):
    """
    Load the dictionary and organize it for efficient lookup.
    It returns a tuple: (sorted_by_length, single_word_map).
    'sorted_by_length' is a list of entries sorted by the length of their Greek phrase
    in descending order, useful for multi-word phrases.
    'single_word_map' is a direct mapping for single-word lookups.
    """
    with open(dict_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Sort by longest Greek phrase first for multi-word matching
    sorted_data = sorted(data, key=lambda d: len(d["greek_word"].split()), reverse=True)

    # Create a direct map for single words for faster lookup
    single_word_map = {
        entry["greek_word"].lower(): entry["cypriot_word"]
        for entry in data if len(entry["greek_word"].split()) == 1
    }

    return sorted_data, single_word_map

def tokenize_text(text):
    """
    Tokenizes Greek text into words and punctuation, preserving original capitalization.
    """
    # Use re.IGNORECASE for case-insensitive matching if needed, but not for splitting
    return re.findall(r'\b\w+\b|[^\w\s]', text, re.UNICODE)

def convert_to_cypriot(text, dictionary_data):
    """
    Converts Modern Greek text to Cypriot Greek.
    Prioritizes matching longer phrases first to avoid partial matches.
    Handles capitalization of the first word in a matched phrase.
    """
    sorted_dictionary, single_word_map = dictionary_data
    tokens = tokenize_text(text)
    converted_tokens = []
    i = 0

    while i < len(tokens):
        current_token = tokens[i]
        lower_current_token = current_token.lower()
        matched = False

        # 1. Try to match multi-word phrases (longest first)
        for entry in sorted_dictionary:
            greek_phrase = entry["greek_word"]
            cypriot_phrase = entry["cypriot_word"]
            greek_phrase_words = greek_phrase.split()

            # Check if the current sequence of tokens matches the Greek phrase
            if i + len(greek_phrase_words) <= len(tokens):
                current_sequence = " ".join(tokens[i : i + len(greek_phrase_words)]).lower()
                if current_sequence == greek_phrase.lower():
                    # Preserve capitalization of the first word in the matched sequence
                    if tokens[i][0].isupper():
                        cypriot_phrase = cypriot_phrase.capitalize()
                    converted_tokens.append(cypriot_phrase)
                    i += len(greek_phrase_words)
                    matched = True
                    break # Matched, move to the next part of the text

        if matched:
            continue

        # 2. If no multi-word phrase matched, try single-word lookup
        if lower_current_token in single_word_map:
            replacement = single_word_map[lower_current_token]
            if current_token[0].isupper():
                replacement = replacement.capitalize()
            converted_tokens.append(replacement)
        else:
            # 3. If no match, keep the original token
            converted_tokens.append(current_token)
        i += 1

    return " ".join(converted_tokens)

# === Example Usage ===
if __name__ == "__main__":
    greek_text_1 = "στην κύπρο και προσπαθείς να βρεις μια"

    dict_path = "cylingo_lexicon.json" 

    try:
        dictionary = load_dictionary(dict_path)

        print(f"Original: {greek_text_1}")
        cypriot_text_1 = convert_to_cypriot(greek_text_1, dictionary)
        print(f"Cypriot: {cypriot_text_1}\n")

    except FileNotFoundError:
        print(f"❌ Error: The dictionary file '{dict_path}' was not found. Please ensure it exists.")
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{dict_path}'. Please check the file's format.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")