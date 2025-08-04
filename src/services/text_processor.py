# src/services/text_processor.py
import re
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import settings
from src.utils.exceptions import TextProcessingError


class TextProcessor:
    """Handles all text processing operations using BERT sentence transformers"""

    def __init__(self, bert_model_name: str = None):
        self.bert_model_name = bert_model_name or getattr(
            settings, "bert_model", "all-MiniLM-L6-v2"
        )
        self.sentence_transformer = None
        self._load_models()

    def _load_models(self):
        """Load sentence transformer models"""
        try:
            self.sentence_transformer = SentenceTransformer(self.bert_model_name)
            print(f"Loaded sentence transformer: {self.bert_model_name}")
        except Exception as e:
            raise TextProcessingError(
                f"Could not load sentence transformer model '{self.bert_model_name}'. "
                f"Error: {e}. Please install with: pip install sentence-transformers"
            ) from e

    def preprocess_text(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive text preprocessing with BERT embeddings
        Returns processed text and extracted features
        """
        if not text or not text.strip():
            raise TextProcessingError("Input text cannot be empty")

        # Basic cleaning
        cleaned_text = self._clean_text(text)

        # Get BERT embedding
        bert_embedding = self.get_text_vector(text)

        # Extract features
        result = {
            "original": text,
            "cleaned": cleaned_text,
            "vector": bert_embedding,
            "vector_dim": len(bert_embedding),
        }

        return result

    def _clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        # Convert to lowercase
        text = text.lower()

        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s\.\!\?\,\-']", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def get_text_vector(self, text: str) -> List[float]:
        """Get BERT vector representation of text"""
        if not text or not text.strip():
            return [0.0] * self.sentence_transformer.get_sentence_embedding_dimension()

        embedding = self.sentence_transformer.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def get_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts using BERT embeddings"""
        if not text1.strip() or not text2.strip():
            return 0.0

        embeddings = self.sentence_transformer.encode(
            [text1, text2], convert_to_tensor=False
        )

        # Calculate cosine similarity
        similarity_matrix = cosine_similarity([embeddings[0]], [embeddings[1]])
        return float(similarity_matrix[0][0])

    def get_batch_similarities(
        self, query_text: str, candidate_texts: List[str]
    ) -> List[float]:
        """Efficiently calculate similarities between query and multiple candidates"""
        if not query_text.strip() or not candidate_texts:
            return [0.0] * len(candidate_texts)

        # Filter out empty texts
        valid_texts = [
            text if text and text.strip() else " " for text in candidate_texts
        ]
        all_texts = [query_text] + valid_texts

        # Get embeddings for all texts at once (more efficient)
        embeddings = self.sentence_transformer.encode(
            all_texts, convert_to_tensor=False
        )

        query_embedding = embeddings[0:1]  # First embedding
        candidate_embeddings = embeddings[1:]  # Rest of embeddings

        # Calculate similarities
        similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
        return similarities.tolist()

    def extract_keywords(self, text: str, n_keywords: int = 5) -> List[str]:
        """Extract important keywords from text using regex"""
        # Simple regex to find words, excluding very short words
        words = re.findall(r"\b\w{3,}\b", text.lower())

        # A simple stopword list
        stopwords = set(
            [
                "the",
                "a",
                "an",
                "in",
                "to",
                "for",
                "of",
                "on",
                "with",
                "is",
                "are",
                "was",
                "were",
            ]
        )

        keywords = [word for word in words if word not in stopwords]

        # For simplicity, returning the first n keywords found
        return keywords[:n_keywords]

    def batch_process_texts(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Process multiple texts efficiently with batch BERT encoding"""
        if not texts:
            return []

        # Filter and prepare texts
        valid_texts = []
        text_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                text_indices.append(i)

        results = [None] * len(texts)

        if valid_texts:
            # Batch encode with BERT for efficiency
            bert_embeddings = self.sentence_transformer.encode(
                valid_texts,
                convert_to_tensor=False,
                show_progress_bar=len(valid_texts) > 100,
            )

            # Process each valid text
            for idx, (text_idx, text) in enumerate(zip(text_indices, valid_texts)):
                try:
                    # Basic cleaning
                    cleaned_text = self._clean_text(text)

                    # Use pre-computed BERT embedding
                    bert_embedding = bert_embeddings[idx].tolist()

                    result = {
                        "original": text,
                        "cleaned": cleaned_text,
                        "vector": bert_embedding,
                        "vector_dim": len(bert_embedding),
                    }

                    results[text_idx] = result

                except Exception as e:
                    text_preview = str(text)[:50] if text is not None else "None"
                    print(f"Error processing text '{text_preview}...': {e}")
                    results[text_idx] = {
                        "original": text,
                        "error": str(e),
                        "vector": [0.0]
                        * self.sentence_transformer.get_sentence_embedding_dimension(),
                        "vector_dim": self.sentence_transformer.get_sentence_embedding_dimension(),
                    }

        # Fill in results for invalid texts
        for i, result in enumerate(results):
            if result is None:
                results[i] = {
                    "original": texts[i],
                    "error": "Empty or invalid text",
                    "vector": [0.0]
                    * self.sentence_transformer.get_sentence_embedding_dimension(),
                    "vector_dim": self.sentence_transformer.get_sentence_embedding_dimension(),
                }

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded models"""
        return {
            "bert_model_name": self.bert_model_name,
            "bert_vector_size": self.sentence_transformer.get_sentence_embedding_dimension(),
            "bert_max_seq_length": self.sentence_transformer.max_seq_length,
        }

    def find_most_similar(
        self, query: str, candidates: List[str], top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find the most similar texts to a query"""
        if not candidates:
            return []

        similarities = self.get_batch_similarities(query, candidates)

        # Create (text, similarity) pairs and sort by similarity
        text_sim_pairs = list(zip(candidates, similarities))
        text_sim_pairs.sort(key=lambda x: x[1], reverse=True)

        return text_sim_pairs[:top_k]


# Create singleton instance
text_processor = TextProcessor()
