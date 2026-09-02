import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticMatcher:
    """
    Singleton class to load the embedding model once and compute semantic similarity.
    Runs 100% locally on your CPU for free.
    """
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            print(f"Loading local embedding model: {model_name}...")
            cls._model = SentenceTransformer(model_name)
        return cls._model

    @classmethod
    def calculate_similarity(cls, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
            
        model = cls.get_model()
        # Convert text to vector embeddings
        embeddings = model.encode([text1, text2])
        
        # Calculate cosine similarity between the two vectors
        sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(sim)