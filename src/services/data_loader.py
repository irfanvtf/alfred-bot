# src/services/data_loader.py
import logging
from typing import Dict
from src.services.knowledge_manager import KnowledgeManager
from src.services.vector_search import vector_search_service


logger = logging.getLogger(__name__)

LANGUAGE_CONFIG = {
    "en": {
        "main_source": "data/sources/en/dialog-en.json",
        "fallback_source": "data/fallback/en/fallback-responses.json",
        "description": "English Dialog",
    },
    "ms": {
        "main_source": "data/sources/ms/dialog-ms.json",
        "fallback_source": "data/fallback/ms/fallback-responses.json",
        "description": "Malay Dialog",
    },
}


def initialize_all_knowledge_collections(
    persist_path: str = "./data/chroma_db",
    languages: Dict[str, Dict[str, str]] = LANGUAGE_CONFIG,
) -> None:
    """
    Initializes and indexes knowledge for all configured languages into separate Chroma collections.
    Collections will be named 'intent_{language_code}' (e.g., 'intent_en', 'intent_ms').
    This function should be called once during application startup.
    """
    logger.info("Starting initialization of all knowledge collections...")

    try:
        knowledge_manager = KnowledgeManager()
        vector_service = vector_search_service
        vector_service.persist_path = persist_path
        vector_service.initialize()

        for lang_code, config in languages.items():
            try:
                main_source_path = config["main_source"]
                fallback_source_path = config["fallback_source"]
                description = config["description"]

                identifier_main = f"{lang_code}_main"
                identifier_fallback = f"{lang_code}_fallback"

                knowledge_manager.register_knowledge_source(
                    identifier_main, main_source_path
                )
                knowledge_manager.register_knowledge_source(
                    identifier_fallback, fallback_source_path
                )

                knowledge_manager.load_knowledge_base(identifier_main)
                kb_data = knowledge_manager.get_knowledge_base_data(identifier_main)

                if not kb_data:
                    logger.error(
                        f"Failed to load or get data for main knowledge base of language '{lang_code}'. Skipping."
                    )
                    continue

                intent_count = len(kb_data.get("intents", []))
                logger.info(
                    f"Loaded knowledge base for '{lang_code}' with {intent_count} intents"
                )

                collection_name = f"intent_{lang_code}"

                source_metadata = {"language": lang_code, "description": description}
                vector_service.index_knowledge_base(
                    collection_name, kb_data, source_metadata=source_metadata
                )
                logger.info(
                    f"Successfully indexed data for language '{lang_code}' into collection '{collection_name}'."
                )

            except Exception as e:
                logger.error(
                    f"Failed to process language '{lang_code}': {e}", exc_info=True
                )
                continue

        logger.info("Completed initialization of all knowledge collections.")

    except Exception as e:
        logger.error(
            f"Critical error during knowledge collection initialization: {e}",
            exc_info=True,
        )
        raise
