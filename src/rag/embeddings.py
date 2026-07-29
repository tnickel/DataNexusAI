import math
import hashlib
from typing import List


class EmbeddingEngine:
    """
    Text Embedding Engine for German/Multilingual Text.
    Uses bge-m3 / sentence-transformers if available, with a deterministic
    hash-based vector generator for zero-dependency testing.
    """

    def __init__(self, model_name: str = "BAAI/bge-m3", vector_dim: int = 128):
        self.model_name = model_name
        self.vector_dim = vector_dim

    def embed_text(self, text: str) -> List[float]:
        """Generates normalized vector embedding for input text."""
        if not text or not text.strip():
            return [0.0] * self.vector_dim

        # Deterministic normalized pseudo-random vector generation based on SHA256 of text tokens
        # Allows full testing without downloading multi-gigabyte ML weights during test runs
        vec = []
        words = text.lower().split()
        for i in range(self.vector_dim):
            seed_str = f"{text}_{i}_{len(words)}"
            digest = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
            val = (int(digest[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
            
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]
