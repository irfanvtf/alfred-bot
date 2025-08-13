# src/services/text_processor.py
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import settings
from src.utils.exceptions import TextProcessingError

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles all text processing operations using BERT sentence transformers"""

    def __init__(
        self,
        bert_model_name: str = None,
        sentence_transformer: "SentenceTransformer" = None,
    ):
        self.bert_model_name = bert_model_name or getattr(
            settings, "bert_model", "paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.sentence_transformer = sentence_transformer
        if not self.sentence_transformer:
            self._load_models()

    def _load_models(self):
        """Load sentence transformer models"""
        try:
            self.sentence_transformer = SentenceTransformer(self.bert_model_name)
            logger.info(f"Loaded sentence transformer: {self.bert_model_name}")
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

        cleaned_text = self._clean_text(text)
        bert_embedding = self.get_text_vector(cleaned_text)

        result = {
            "original": text,
            "cleaned": cleaned_text,
            "vector": bert_embedding,
            "vector_dim": len(bert_embedding),
        }

        return result

    def _clean_text(self, text: str) -> str:
        """Basic text cleaning - preserve semantic meaning while ensuring consistency with patterns"""
        text = text.lower()
        text = re.sub(r"[.!?,;:]", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        return text

    def get_text_vector(self, text: str) -> List[float]:
        """Get BERT vector representation of text"""
        if not text or not text.strip():
            logger.warning("Empty text provided for vector generation")
            return [0.0] * self.sentence_transformer.get_sentence_embedding_dimension()

        embedding = self.sentence_transformer.encode(
            text, convert_to_tensor=False, show_progress_bar=False
        )
        return embedding.tolist()

    def get_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts using BERT embeddings"""
        if not text1.strip() or not text2.strip():
            return 0.0

        embeddings = self.sentence_transformer.encode(
            [text1, text2], convert_to_tensor=False, show_progress_bar=False
        )

        similarity_matrix = cosine_similarity([embeddings[0]], [embeddings[1]])
        similarity = float(similarity_matrix[0][0])
        return similarity

    def get_batch_similarities(
        self, query_text: str, candidate_texts: List[str]
    ) -> List[float]:
        """Efficiently calculate similarities between query and multiple candidates"""
        if not query_text.strip() or not candidate_texts:
            return [0.0] * len(candidate_texts)

        valid_texts = [
            text if text and text.strip() else " " for text in candidate_texts
        ]
        all_texts = [query_text] + valid_texts

        embeddings = self.sentence_transformer.encode(
            all_texts, convert_to_tensor=False, show_progress_bar=False
        )

        query_embedding = embeddings[0:1]
        candidate_embeddings = embeddings[1:]

        similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
        return similarities.tolist()

    def extract_keywords(self, text: str, n_keywords: int = 5) -> List[str]:
        """Extract important keywords from text using regex"""
        words = re.findall(r"\b\w{3,}\b", text.lower())

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
        return keywords[:n_keywords]

    def batch_process_texts(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Process multiple texts efficiently with batch BERT encoding"""
        if not texts:
            return []

        valid_texts = []
        text_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                text_indices.append(i)

        results = [None] * len(texts)

        if valid_texts:
            bert_embeddings = self.sentence_transformer.encode(
                valid_texts,
                convert_to_tensor=False,
                show_progress_bar=False,
            )

            for idx, (text_idx, text) in enumerate(zip(text_indices, valid_texts)):
                try:
                    cleaned_text = self._clean_text(text)
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

        text_sim_pairs = list(zip(candidates, similarities))
        text_sim_pairs.sort(key=lambda x: x[1], reverse=True)

        return text_sim_pairs[:top_k]

    def enhance_query_with_context(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """Enhance query with conversation context"""
        if not context:
            return query

        enhanced_query = query

        history = context.get("conversation_history", [])
        if history:
            recent_messages = [
                msg["message"] for msg in history[-3:] if msg.get("role") == "user"
            ]
            if recent_messages:
                context_text = " ".join(recent_messages[-2:])
                enhanced_query = f"{context_text} {query}"

        context_vars = context.get("context_variables", {})
        if context_vars:
            context_parts = []
            for key, value in context_vars.items():
                if isinstance(value, str) and len(value) < 50:
                    context_parts.append(value)
            if context_parts:
                context_text = " ".join(context_parts)
                enhanced_query = f"{enhanced_query} {context_text}"

        return enhanced_query


text_processor = TextProcessor()
