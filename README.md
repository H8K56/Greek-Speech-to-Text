# Greek and Cypriot Restaurant Reservation AI

## **Project Overview**
This project is focused on developing an AI system that:
1. **Understands Greek and Cypriot Greek dialects** via fine-tuned Whisper models.
2. Handles **restaurant reservation tasks** with high accuracy.
3. Integrates Automatic Speech Recognition (ASR), Natural Language Processing (NLP), and Dialogue Management modules.

The final product will enable users to make reservations at restaurants in Greek with native-like conversational accuracy.

---

## **System Components**

### **1. Whisper Fine-Tuning**
- **Purpose:** Adapt Whisper for transcribing Greek and Cypriot Greek speech.
- **Datasets:**
  - [Mozilla Common Voice (Greek)](https://commonvoice.mozilla.org/)
  - [Greek Podcast Corpus](https://github.com/)
  - SpeechDat-II and Orientel (Cypriot Greek-specific data)
- **Steps:**
  - Preprocess datasets for audio-text alignment.
  - Fine-tune Whisper for Greek and Cypriot dialects.

### **2. NLP Models**
- **Intent Recognition:** Detect intents like creating, modifying, or canceling reservations.
- **Entity Extraction:** Extract reservation details (e.g., date, time, number of people).
- **Tools:**
  - Hugging Face Transformers (fine-tuned for Greek text)
  - spaCy for Named Entity Recognition (NER)

### **3. Dialogue Management**
- **Purpose:** Manage multi-turn dialogues and maintain context.
- **Framework:** Rasa or Dialogflow, configured for Greek.
- **Tasks:**
  - Generate appropriate responses.
  - Handle edge cases (e.g., ambiguous user requests).