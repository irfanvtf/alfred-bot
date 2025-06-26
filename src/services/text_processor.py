# src/services/text_processor.py
import spacy
import re
from typing import List, Dict, Any, Optional, Tuple
from spacy.tokens import Doc
from config.settings import settings
from src.utils.exceptions import TextProcessingError


class TextProcessor:
    """Handles all text processing operations using spaCy"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.spacy_model_md
        self.nlp = None
        self._load_model()

    def _load_model(self):
        """Load the spaCy model"""
        try:
            self.nlp = spacy.load(self.model_name)
        except OSError:
            # Fallback to smaller model
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print(
                    f"Warning: Could not load {self.model_name}, using en_core_web_sm instead"
                )
            except OSError:
                raise TextProcessingError(
                    "No spaCy model found. Please install with: python -m spacy download en_core_web_md"
                )

    def preprocess_text(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive text preprocessing
        Returns processed text and extracted features
        """
        if not text or not text.strip():
            raise TextProcessingError("Input text cannot be empty")

        # Basic cleaning
        cleaned_text = self._clean_text(text)

        # Process with spaCy
        doc = self.nlp(cleaned_text)

        # Extract features
        result = {
            "original": text,
            "cleaned": cleaned_text,
            "tokens": [token.text for token in doc],
            "lemmas": [
                token.lemma_
                for token in doc
                if not token.is_stop and not token.is_punct
            ],
            "pos_tags": [(token.text, token.pos_) for token in doc],
            "entities": [(ent.text, ent.label_) for ent in doc.ents],
            "vector": doc.vector,
            "vector_norm": doc.vector_norm,
            "processed_doc": doc,  # Keep for further processing
        }

        return result

    def _clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        # Convert to lowercase
        text = text.lower()

        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s\.\!\?\,\-\']", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def get_text_vector(self, text: str) -> List[float]:
        """Get vector representation of text"""
        doc = self.nlp(text)
        return doc.vector.tolist()

    def get_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)

        # Handle empty vectors
        if doc1.vector_norm == 0 or doc2.vector_norm == 0:
            return 0.0

        return doc1.similarity(doc2)

    def extract_keywords(self, text: str, n_keywords: int = 5) -> List[str]:
        """Extract important keywords from text"""
        doc = self.nlp(text)

        # Filter tokens: no stop words, punctuation, or short words
        keywords = [
            token.lemma_.lower()
            for token in doc
            if not token.is_stop
            and not token.is_punct
            and not token.is_space
            and len(token.text) > 2
            and token.pos_
            in ["NOUN", "VERB", "ADJ"]  # Focus on meaningful parts of speech
        ]

        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for keyword in keywords:
            if keyword not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword)

        return unique_keywords[:n_keywords]

    def batch_process_texts(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Process multiple texts efficiently"""
        if not texts:
            return []

        results = []
        for text in texts:
            try:
                result = self.preprocess_text(text)
                results.append(result)
            except Exception as e:
                # Handle None and other problematic text values safely
                text_preview = str(text)[:50] if text is not None else "None"
                print(f"Error processing text '{text_preview}...': {e}")
                # Add error result
                results.append(
                    {
                        "original": text,
                        "error": str(e),
                        "vector": [0.0] * self.nlp.vocab.vectors_length,
                    }
                )

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "language": self.nlp.lang,
            "vector_size": self.nlp.vocab.vectors_length,
            "n_vectors": len(self.nlp.vocab.vectors),
            "pipeline_components": self.nlp.pipe_names,
        }
