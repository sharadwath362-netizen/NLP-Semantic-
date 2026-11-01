"""
build_cleaned_word_bank.py
──────────────────────────
Reads data/word_bank.json and produces data/cleaned_word_bank.json
containing ONLY:
  • Single words  (no spaces, underscores, or hyphens in the key)
  • Length ≤ 8 characters
  • Entries that are dicts (valid word entries, not syntactic-frame labels)

All synset keys referenced by the kept words are also carried over
unchanged so the GameEngine can still resolve definitions / examples.
No code in game_engine.py or anywhere else is modified.
"""

import json
import sys

SRC  = "data/word_bank.json"
DEST = "data/cleaned_word_bank.json"
SYNSET_SUFFIXES = ("-n", "-v", "-a", "-r", "-s")

def is_synset_key(key: str) -> bool:
    return key.endswith(SYNSET_SUFFIXES)

def is_valid_word_key(key: str) -> bool:
    """Single word, no spaces/underscores/hyphens, length 1–8, dict value."""
    return (
        " "  not in key and
        "_"  not in key and
        "-"  not in key and
        1 < len(key) <= 8           # length >1 matches game_engine.py filter
    )

def collect_referenced_synsets(data: dict, kept_words: list[str]) -> set[str]:
    """Walk every kept word entry and collect synset IDs it references."""
    refs: set[str] = set()
    for word in kept_words:
        entry = data[word]
        if not isinstance(entry, dict):
            continue
        for pos_details in entry.values():
            if not isinstance(pos_details, dict):
                continue
            senses = pos_details.get("sense", [])
            if not isinstance(senses, list):
                continue
            for sense in senses:
                if isinstance(sense, dict) and "synset" in sense:
                    refs.add(sense["synset"])
    return refs

def main():
    print(f"Loading {SRC} …")
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_keys = list(data.keys())
    print(f"  Total keys in source   : {len(all_keys):,}")

    # ── 1. Separate synset keys from word keys ──────────────────────────────
    all_synset_keys = [k for k in all_keys if is_synset_key(k)]
    all_word_keys   = [k for k in all_keys if not is_synset_key(k)]
    print(f"  Synset keys            : {len(all_synset_keys):,}")
    print(f"  Word keys              : {len(all_word_keys):,}")

    # ── 2. Filter word keys ─────────────────────────────────────────────────
    kept_words = [
        w for w in all_word_keys
        if is_valid_word_key(w) and isinstance(data[w], dict)
    ]
    removed_multi   = [w for w in all_word_keys if (" " in w or "_" in w or "-" in w)]
    removed_long    = [w for w in all_word_keys if not any(c in w for c in " _-") and len(w) > 8]
    removed_nondict = [w for w in all_word_keys if not isinstance(data[w], dict)]

    print()
    print("── Word filtering ──────────────────────────────────────")
    print(f"  Multi-word removed      : {len(removed_multi):,}")
    print(f"  Length > 8 removed      : {len(removed_long):,}")
    print(f"  Non-dict removed        : {len(removed_nondict):,}")
    print(f"  Words KEPT              : {len(kept_words):,}")

    # ── 3. Collect only synsets referenced by kept words ────────────────────
    print()
    print("Collecting synset references …")
    referenced = collect_referenced_synsets(data, kept_words)
    needed_synsets = [k for k in all_synset_keys if k in referenced]
    orphan_synsets = len(all_synset_keys) - len(needed_synsets)

    print(f"  Unique synsets referenced by kept words : {len(referenced):,}")
    print(f"  Synset keys carried over                : {len(needed_synsets):,}")
    print(f"  Orphan synset keys dropped              : {orphan_synsets:,}")

    # ── 4. Build output dict (words first, then synsets — same structure) ───
    print()
    print("Building output dict …")
    cleaned: dict = {}

    for word in kept_words:
        cleaned[word] = data[word]

    for synset_key in needed_synsets:
        cleaned[synset_key] = data[synset_key]

    total_out = len(cleaned)
    print(f"  Total keys in cleaned  : {total_out:,}  ({len(kept_words):,} words + {len(needed_synsets):,} synsets)")

    # ── 5. Write output ─────────────────────────────────────────────────────
    print()
    print(f"Writing {DEST} …")
    with open(DEST, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print()
    print("═" * 56)
    print(f"  Done!  →  {DEST}")
    print(f"  Words  : {len(kept_words):,}")
    print(f"  Synsets: {len(needed_synsets):,}")
    print(f"  Total  : {total_out:,} keys")
    print("═" * 56)

if __name__ == "__main__":
    main()
