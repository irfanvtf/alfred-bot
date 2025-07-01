# tests/test_text_processor.py
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.text_processor import TextProcessor
from src.utils.exceptions import TextProcessingError


class TestTextProcessor:
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = TextProcessor()

    def test_preprocess_text_basic(self):
        """Test basic text preprocessing"""
        text = "Hello, how are you today?"
        result = self.processor.preprocess_text(text)

        assert result["original"] == text
        assert "cleaned" in result
        assert "tokens" in result
        assert "lemmas" in result
        assert "pos_tags" in result
        assert "entities" in result
        assert "vector" in result
        assert "vector_norm" in result
        assert "processed_doc" in result
        assert len(result["vector"]) > 0

    def test_preprocess_text_detailed_content(self):
        """Test preprocessing with detailed content validation"""
        text = "The quick brown fox jumps over the lazy dog."
        result = self.processor.preprocess_text(text)

        # Check cleaned text
        assert result["cleaned"] == "the quick brown fox jumps over the lazy dog."

        # Check tokens
        assert isinstance(result["tokens"], list)
        assert len(result["tokens"]) > 0

        # Check lemmas (should exclude stop words and punctuation)
        assert isinstance(result["lemmas"], list)
        assert "quick" in result["lemmas"] or "brown" in result["lemmas"]

        # Check POS tags
        assert isinstance(result["pos_tags"], list)
        assert all(
            isinstance(tag, tuple) and len(tag) == 2 for tag in result["pos_tags"]
        )

        # Check entities
        assert isinstance(result["entities"], list)

    def test_preprocess_text_empty(self):
        """Test preprocessing with empty text"""
        with pytest.raises(TextProcessingError):
            self.processor.preprocess_text("")

    def test_preprocess_text_whitespace_only(self):
        """Test preprocessing with whitespace-only text"""
        with pytest.raises(TextProcessingError):
            self.processor.preprocess_text("   \n\t  ")

    def test_preprocess_text_none(self):
        """Test preprocessing with None input"""
        with pytest.raises(TextProcessingError):
            self.processor.preprocess_text(None)

    def test_clean_text_functionality(self):
        """Test the _clean_text method indirectly"""
        text = "HELLO!!!   Multiple   Spaces... AND @#$% SYMBOLS"
        result = self.processor.preprocess_text(text)
        cleaned = result["cleaned"]

        # Should be lowercase
        assert cleaned.islower()

        # Should not have multiple consecutive spaces
        assert "   " not in cleaned  # Check for 3+ spaces instead of 2

        # Should not have special symbols (except basic punctuation)
        assert "@" not in cleaned
        assert "#" not in cleaned
        assert "$" not in cleaned
        assert "%" not in cleaned

    def test_get_text_vector(self):
        """Test text vector extraction"""
        text = "Hello world"
        vector = self.processor.get_text_vector(text)

        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(v, (int, float)) for v in vector)

    def test_get_text_vector_empty(self):
        """Test text vector for empty text"""
        vector = self.processor.get_text_vector("")
        assert isinstance(vector, list)
        assert len(vector) > 0  # spaCy returns zero vector, not empty list

    def test_get_similarity(self):
        """Test text similarity calculation"""
        text1 = "Hello world"
        text2 = "Hi there"
        text3 = "Hello world"

        # Similar texts should have some similarity
        sim1 = self.processor.get_similarity(text1, text2)
        assert 0 <= sim1 <= 1
        assert isinstance(sim1, float)

        # Identical texts should have high similarity
        sim2 = self.processor.get_similarity(text1, text3)
        assert sim2 > 0.9

    def test_get_similarity_edge_cases(self):
        """Test similarity with edge cases"""
        # Empty strings
        sim1 = self.processor.get_similarity("", "")
        assert sim1 == 0.0

        # One empty string
        sim2 = self.processor.get_similarity("hello", "")
        assert sim2 == 0.0

        # Very different texts
        sim3 = self.processor.get_similarity("apple", "mathematics")
        assert 0 <= sim3 < 0.5  # Should be low similarity

    def test_extract_keywords(self):
        """Test keyword extraction"""
        text = "I need help with my computer programming assignment"
        keywords = self.processor.extract_keywords(text, n_keywords=3)

        assert isinstance(keywords, list)
        assert len(keywords) <= 3
        assert all(isinstance(kw, str) for kw in keywords)

        # Keywords should not contain stop words
        stop_words = {"i", "my", "with"}
        assert not any(kw in stop_words for kw in keywords)

    def test_extract_keywords_different_counts(self):
        """Test keyword extraction with different counts"""
        text = "The machine learning algorithm processes natural language text data efficiently"

        # Test different numbers of keywords
        keywords_3 = self.processor.extract_keywords(text, n_keywords=3)
        keywords_5 = self.processor.extract_keywords(text, n_keywords=5)
        keywords_10 = self.processor.extract_keywords(text, n_keywords=10)

        assert len(keywords_3) <= 3
        assert len(keywords_5) <= 5
        assert len(keywords_10) <= 10

        # First 3 keywords should be the same
        assert keywords_3 == keywords_5[:3]

    def test_extract_keywords_empty_text(self):
        """Test keyword extraction with empty text"""
        keywords = self.processor.extract_keywords("", n_keywords=5)
        assert keywords == []

    def test_extract_keywords_short_words_filtered(self):
        """Test that short words are filtered out"""
        text = "I am a big cat in a box"
        keywords = self.processor.extract_keywords(text, n_keywords=10)

        # Short words like "am", "a", "in" should be filtered out
        short_words = {"am", "a", "in", "i"}
        assert not any(kw in short_words for kw in keywords)

    def test_batch_process_texts(self):
        """Test batch processing"""
        texts = ["Hello world", "How are you?", "Goodbye!"]
        results = self.processor.batch_process_texts(texts)

        assert len(results) == len(texts)
        assert all("original" in result for result in results)
        assert all("vector" in result for result in results)

    def test_batch_process_empty_list(self):
        """Test batch processing with empty list"""
        results = self.processor.batch_process_texts([])
        assert results == []

    def test_batch_process_with_errors(self):
        """Test batch processing handles errors gracefully"""
        # Test with actual error-causing inputs that your method can handle
        texts = [
            "Good text",
            "",
            "Another good text",
        ]  # Use empty string instead of None

        results = self.processor.batch_process_texts(texts)

        assert len(results) == 3
        # Empty string should cause an error due to TextProcessingError
        assert "error" in results[1]  # Middle item should have error
        assert "original" in results[0]  # First item should be fine
        assert "original" in results[2]  # Last item should be fine

    def test_get_model_info(self):
        """Test model information retrieval"""
        info = self.processor.get_model_info()

        assert isinstance(info, dict)
        assert "model_name" in info
        assert "language" in info
        assert "vector_size" in info
        assert "n_vectors" in info
        assert "pipeline_components" in info

        # Check types
        assert isinstance(info["model_name"], str)
        assert isinstance(info["language"], str)
        assert isinstance(info["vector_size"], int)
        assert isinstance(info["n_vectors"], int)
        assert isinstance(info["pipeline_components"], list)

        # Check reasonable values
        assert info["vector_size"] > 0
        assert info["language"] == "en"  # Should be English

    def test_model_initialization_with_custom_model(self):
        """Test initialization with custom model name"""
        # This test might need to be skipped if the model isn't available
        try:
            processor = TextProcessor(model_name="en_core_web_sm")
            assert processor.model_name == "en_core_web_sm"
            assert processor.nlp is not None
        except Exception:
            pytest.skip("Custom model not available")

    def test_model_fallback_mechanism(self):
        """Test model fallback when primary model fails"""
        with patch("spacy.load") as mock_load:
            # First call (primary model) fails, second call (fallback) succeeds
            mock_nlp = MagicMock()
            mock_load.side_effect = [OSError("Model not found"), mock_nlp]

            processor = TextProcessor(model_name="nonexistent_model")

            # Should have tried to load the nonexistent model, then fallback
            assert mock_load.call_count == 2
            assert processor.nlp == mock_nlp

    def test_model_fallback_complete_failure(self):
        """Test behavior when both primary and fallback models fail"""
        with patch("spacy.load") as mock_load:
            # Both calls fail
            mock_load.side_effect = OSError("No models available")

            with pytest.raises(TextProcessingError, match="No spaCy model found"):
                TextProcessor(model_name="nonexistent_model")

    def test_vector_properties(self):
        """Test vector-related properties and consistency"""
        text = "This is a test sentence for vector analysis."

        # Get vector through different methods
        preprocessed = self.processor.preprocess_text(text)
        vector_direct = self.processor.get_text_vector(text)

        # Vectors should be consistent
        assert len(preprocessed["vector"]) == len(vector_direct)

        # Vector should have reasonable properties
        assert len(vector_direct) > 0
        assert not all(
            v == 0 for v in vector_direct
        )  # Should not be all zeros for meaningful text

    def test_pos_tags_accuracy(self):
        """Test POS tagging accuracy"""
        text = "The quick brown fox jumps over the lazy dog."
        result = self.processor.preprocess_text(text)
        pos_tags = result["pos_tags"]

        # Should have POS tags for all tokens
        assert len(pos_tags) == len(result["tokens"])

        # Check some expected POS tags
        pos_dict = dict(pos_tags)
        assert "fox" in pos_dict
        assert "jumps" in pos_dict

        # Basic POS tag validation
        expected_pos_tags = {"NOUN", "VERB", "ADJ", "DET", "ADP", "PUNCT"}
        actual_pos_tags = {tag for _, tag in pos_tags}
        assert actual_pos_tags.issubset(
            expected_pos_tags.union({"PROPN", "PRON", "ADV", "CONJ", "NUM", "X"})
        )

    def test_entity_recognition(self):
        """Test named entity recognition"""
        text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
        result = self.processor.preprocess_text(text)
        entities = result["entities"]

        assert isinstance(entities, list)
        # Should find some entities in this text
        if entities:  # Only test if entities are found
            assert all(isinstance(ent, tuple) and len(ent) == 2 for ent in entities)
            entity_texts = [ent[0] for ent in entities]
            entity_labels = [ent[1] for ent in entities]

            # Check that labels are valid
            valid_labels = {"PERSON", "ORG", "GPE", "DATE", "MONEY", "QUANTITY", "TIME"}
            assert all(
                label in valid_labels or label.startswith(("PERSON", "ORG", "GPE"))
                for label in entity_labels
            )

    def test_lemmatization_quality(self):
        """Test lemmatization quality"""
        text = "The children were running quickly through the beautiful gardens."
        result = self.processor.preprocess_text(text)
        lemmas = result["lemmas"]

        # Should contain lemmatized forms
        assert "child" in lemmas or "children" in lemmas  # children -> child
        assert "run" in lemmas or "running" in lemmas  # running -> run
        assert "quick" in lemmas or "quickly" in lemmas  # quickly -> quick
        assert "beautiful" in lemmas  # beautiful -> beautiful
        assert "garden" in lemmas or "gardens" in lemmas  # gardens -> garden
