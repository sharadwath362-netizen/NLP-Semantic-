import json
import os
import ssl
import numpy as np
import gensim.downloader as api

# Bypass unverified SSL context issues common on macOS / corporate proxies
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


class EmbeddingEngine:
    def __init__(self, model_name: str = "glove-wiki-gigaword-50"):
        """Initializes and loads the pre-trained embedding model."""
        print(f"Loading embedding model: '{model_name}'...")
        try:
            self.model = api.load(model_name)
            self.is_ready = True
            print("Embedding model loaded successfully.")
        except Exception as e:
            print(f"Failed to load embedding model: {e}")
            self.model = None
            self.is_ready = False

        # In-memory vector cache: { "word": np.ndarray }
        self.word_vectors: dict[str, np.ndarray] = {}

    def get_vector(self, word: str) -> np.ndarray | None:
        """Retrieves the vector for a single word, using cache if available."""
        if not self.is_ready or not word:
            return None

        clean_word = word.strip().lower()

        # Check local cache first
        if clean_word in self.word_vectors:
            return self.word_vectors[clean_word]

        # Check pre-trained model vocabulary
        if clean_word in self.model:
            vector = self.model[clean_word]
            self.word_vectors[clean_word] = vector
            return vector

        return None

    def build_dataset_vectors(self, word_bank_path: str = "data/word_bank.json") -> int:
        """
        Reads words from word_bank.json, filters out synset IDs,
        and converts all valid words into cached vectors.
        """
        if not self.is_ready:
            print("Model not ready. Cannot build vectors.")
            return 0

        if not os.path.exists(word_bank_path):
            print(f"File not found: {word_bank_path}")
            return 0

        with open(word_bank_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Extract only plain words (skipping synset keys like '02193771-s')
        words = [
            k.strip().lower()
            for k in raw_data.keys()
            if not k.endswith(("-n", "-v", "-a", "-r", "-s")) and len(k) > 1
        ]

        converted_count = 0
        for word in words:
            if word in self.model:
                self.word_vectors[word] = self.model[word]
                converted_count += 1

        print(f"Cached {converted_count}/{len(words)} words into vectors.")
        return converted_count

    def compute_similarity(self, word1: str, word2: str) -> float:
        """
        Calculates cosine similarity between two words with calibrated 
        baseline subtraction to eliminate embedding background noise.
        """
        if not self.is_ready or not word1 or not word2:
            return 0.0

        w1 = word1.strip().lower()
        w2 = word2.strip().lower()

        if w1 == w2:
            return 100.0

        # Check if words exist in model vocabulary
        if w1 not in self.model or w2 not in self.model:
            return 0.0


        # 1. Get raw cosine similarity (-1.0 to 1.0)
        raw_sim = float(self.model.similarity(w1, w2))

        # 2. Subtract baseline noise (~0.22 for GloVe-50)
        # GloVe-50 random unrelated words typically sit around 0.20 - 0.25
        baseline = 0.22
        adjusted = max(0.0, (raw_sim - baseline) / (1.0 - baseline))

        # 3. Apply non-linear curve to separate near-matches from weak context
        calibrated_score = (adjusted ** 1.3) * 100.0

        return round(calibrated_score, 2)

if __name__ == "__main__":
    engine = EmbeddingEngine()

    if engine.is_ready:
        # Pre-cache words from data/word_bank.json
        engine.build_dataset_vectors("data/word_bank.json")

        # Test similarity calculations
        sample_pairs = [
            ("king", "monarch"),
            ("dog", "puppy"),
            ("hot", "cold"),
            ("apple", "tractor"),
        ]

        print("\n--- Similarity Verification ---")
        for w1, w2 in sample_pairs:
            sim = engine.compute_similarity(w1, w2)
            print(f"'{w1}' <-> '{w2}' = {sim}%")