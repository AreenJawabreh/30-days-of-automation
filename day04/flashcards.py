"""
Day 4 - #30DaysOfAutomation
Vocabulary Flashcards Builder: English words -> ready-to-study flashcards.

For every word in words.txt, the script asks 3 free APIs (no keys needed):
    1. Free Dictionary API  -> pronunciation, part of speech, definition, example, audio
    2. Datamuse API         -> synonyms
    3. MyMemory API         -> Arabic translation

Then it creates:
    flashcards_YYYY-MM-DD.xlsx  -> a nice table to read and print
    flashcards_anki.csv         -> import into Anki or Quizlet to study

If one API fails or doesn't know a word, the script does NOT crash:
it writes "not available" for that part and moves on to the next word.

Usage:
    python flashcards.py
"""

import csv
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).parent
WORDS_FILE = BASE / "words.txt"
EXCEL_FILE = BASE / f"flashcards_{datetime.now():%Y-%m-%d}.xlsx"
ANKI_FILE = BASE / "flashcards_anki.csv"

NOT_AVAILABLE = "not available"
TIMEOUT = 10  # seconds: never wait forever for an API

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


# ---------- API 1: Free Dictionary ----------
def get_definition(word: str) -> dict:
    """Returns phonetic, part of speech, definition, example and audio link."""
    result = {"phonetic": NOT_AVAILABLE, "part_of_speech": NOT_AVAILABLE,
              "definition": NOT_AVAILABLE, "example": NOT_AVAILABLE, "audio": ""}
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 404:          # the API doesn't know this word
            logging.warning(f"Dictionary: no definition found for '{word}'")
            return result
        response.raise_for_status()               # any other error -> go to except
        entry = response.json()[0]                # the API answers with a LIST

        # Pronunciation and audio: take the first ones that are not empty
        for p in entry.get("phonetics", []):
            if p.get("text") and result["phonetic"] == NOT_AVAILABLE:
                result["phonetic"] = p["text"]
            if p.get("audio") and not result["audio"]:
                result["audio"] = p["audio"]
        if result["phonetic"] == NOT_AVAILABLE and entry.get("phonetic"):
            result["phonetic"] = entry["phonetic"]

        # First meaning and first definition
        meaning = entry["meanings"][0]
        first = meaning["definitions"][0]
        result["part_of_speech"] = meaning.get("partOfSpeech", NOT_AVAILABLE)
        result["definition"] = first.get("definition", NOT_AVAILABLE)
        # Find the first definition that has an example sentence
        for d in meaning["definitions"]:
            if d.get("example"):
                result["example"] = d["example"]
                break
    except Exception as error:
        logging.error(f"Dictionary API failed for '{word}': {error}")
    return result


# ---------- API 2: Datamuse (synonyms) ----------
def get_synonyms(word: str, limit: int = 4) -> str:
    url = "https://api.datamuse.com/words"
    try:
        response = requests.get(url, params={"rel_syn": word, "max": limit}, timeout=TIMEOUT)
        response.raise_for_status()
        synonyms = [item["word"] for item in response.json()]
        return ", ".join(synonyms) if synonyms else NOT_AVAILABLE
    except Exception as error:
        logging.error(f"Datamuse API failed for '{word}': {error}")
        return NOT_AVAILABLE


# ---------- API 3: MyMemory (Arabic translation) ----------
def get_arabic(word: str) -> str:
    url = "https://api.mymemory.translated.net/get"
    try:
        response = requests.get(url, params={"q": word, "langpair": "en|ar"}, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        text = data.get("responseData", {}).get("translatedText", "")
        # If the API can't translate, it sometimes just returns the same English word
        if not text or text.lower() == word.lower():
            return NOT_AVAILABLE
        return text
    except Exception as error:
        logging.error(f"Translation API failed for '{word}': {error}")
        return NOT_AVAILABLE


# ---------- Main ----------
def main() -> None:
    if not WORDS_FILE.exists():
        logging.error(f"Create {WORDS_FILE.name} with one English word per line first.")
        return

    # Read words: remove empty lines, spaces and duplicates, keep the order
    words = list(dict.fromkeys(
        line.strip().lower() for line in WORDS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()
    ))
    logging.info(f"Building flashcards for {len(words)} words...")

    cards = []
    for i, word in enumerate(words, start=1):
        logging.info(f"[{i}/{len(words)}] {word}")
        card = {"word": word}
        card.update(get_definition(word))
        card["synonyms"] = get_synonyms(word)
        card["arabic"] = get_arabic(word)
        cards.append(card)
        time.sleep(0.5)  # be polite: don't send too many requests per second

    df = pd.DataFrame(cards, columns=["word", "arabic", "phonetic", "part_of_speech",
                                      "definition", "example", "synonyms", "audio"])

    # 1) Excel file to read and print
    df.to_excel(EXCEL_FILE, index=False)

    # 2) Anki / Quizlet file: front = word, back = everything to remember
    with open(ANKI_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for card in cards:
            back = (f"{card['arabic']} | ({card['part_of_speech']}) {card['definition']}"
                    f" | Example: {card['example']} | Synonyms: {card['synonyms']}")
            writer.writerow([card["word"], back])

    complete = sum(1 for c in cards if NOT_AVAILABLE not in (c["definition"], c["arabic"], c["synonyms"]))
    logging.info(f"Done! {len(cards)} flashcards created ({complete} complete, "
                 f"{len(cards) - complete} with missing parts).")
    logging.info(f"Excel: {EXCEL_FILE.name} | Anki/Quizlet: {ANKI_FILE.name}")


if __name__ == "__main__":
    main()
