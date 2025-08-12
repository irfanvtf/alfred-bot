# src/services/data_loader.py
import logging
from typing import Dict, Any, List
from src.services.knowledge_manager import KnowledgeManager
from src.services.vector_search import vector_search_service
from src.services.text_processor import text_processor
# Import settings if you have them, otherwise define paths here or pass them as arguments
# from config.settings import settings

logger = logging.getLogger(__name__)

# Configuration for supported languages and their data files
# This could also be read from a config file or environment variables
LANGUAGE_CONFIG = {
    "en": {
        "main_source": "data/sources/en/dialog-en.json",
        "fallback_source": "data/fallback/en/fallback-responses.json",
        "description": "English Dialog"
    },
    "ms": {
        "main_source": "data/sources/ms/dialog-ms.json",
        "fallback_source": "data/fallback/ms/fallback-responses.json",
        "description": "Malay Dialog"
    }
    # Add more languages here as needed
}

def initialize_all_knowledge_collections(
    persist_path: str = "./data/chroma_db",
    languages: Dict[str, Dict[str, str]] = LANGUAGE_CONFIG
) -> None:
    """
    Initializes and indexes knowledge for all configured languages into separate Chroma collections.
    Collections will be named 'intent_{language_code}' (e.g., 'intent_en', 'intent_ms').
    This function should be called once during application startup.
    """
    logger.info("Starting initialization of all knowledge collections...")
    logger.info(f"Persist path: {persist_path}")
    logger.info(f"Languages to process: {list(languages.keys())}")
    
    try:
        # Initialize managers
        knowledge_manager = KnowledgeManager()
        # Use the singleton vector_search_service instance and initialize it
        vector_service = vector_search_service
        vector_service.persist_path = persist_path
        vector_service.initialize() # Initialize the Chroma client

        # Iterate through configured languages
        for lang_code, config in languages.items():
            try:
                logger.info(f"Processing language: {lang_code}")
                
                # 1. Register sources for this language
                main_source_path = config["main_source"]
                fallback_source_path = config["fallback_source"]
                description = config["description"]
                
                identifier_main = f"{lang_code}_main"
                identifier_fallback = f"{lang_code}_fallback"
                
                knowledge_manager.register_knowledge_source(identifier_main, main_source_path)
                knowledge_manager.register_knowledge_source(identifier_fallback, fallback_source_path)
                logger.debug(f"Registered sources for '{lang_code}': main='{main_source_path}', fallback='{fallback_source_path}'")

                # 2. Load the main knowledge base data for this language
                knowledge_manager.load_knowledge_base(identifier_main)
                kb_data = knowledge_manager.get_knowledge_base_data(identifier_main)
                
                if not kb_data:
                    logger.error(f"Failed to load or get data for main knowledge base of language '{lang_code}'. Skipping.")
                    continue
                
                # Log some info about the knowledge base
                intent_count = len(kb_data.get("intents", []))
                logger.info(f"Loaded knowledge base for '{lang_code}' with {intent_count} intents")
                
                # 3. Determine the collection name using the new convention
                collection_name = f"intent_{lang_code}"
                logger.info(f"Indexing data for language '{lang_code}' into collection '{collection_name}'...")

                # 4. Index the knowledge base data into the specific collection
                source_metadata = {
                    "language": lang_code, 
                    "description": description
                }
                vector_service.index_knowledge_base(
                    collection_name, 
                    kb_data, 
                    source_metadata=source_metadata
                )
                logger.info(f"Successfully indexed data for language '{lang_code}' into collection '{collection_name}'.")
                
            except Exception as e:
                logger.error(f"Failed to process language '{lang_code}': {e}", exc_info=True)
                # Depending on requirements, you might want to continue with other languages or stop.
                # For now, let's continue to try other languages.
                continue 
        
        logger.info("Completed initialization of all knowledge collections.")
        
    except Exception as e:
        logger.error(f"Critical error during knowledge collection initialization: {e}", exc_info=True)
        raise # Re-raise critical initialization errors
