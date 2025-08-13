from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import chromadb
from chromadb.config import Settings
from src.services.chroma_service import ChromaService
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ChromaQuery(BaseModel):
    query_texts: List[str]
    n_results: int = 10
    where_filter: Optional[Dict[str, Any]] = None


# Global instance of ChromaService for direct access
_chroma_service_instance: Optional[ChromaService] = None


def get_chroma_client() -> chromadb.Client:
    try:
        # Create Chroma client with persistent storage
        client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
        return client
    except Exception as e:
        logger.error(f"Failed to get Chroma client: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not connect to ChromaDB")


def get_chroma_service(
    client: chromadb.Client = Depends(get_chroma_client),
) -> ChromaService:
    return ChromaService(chroma_client=client)


def get_chroma_service_no_deps() -> ChromaService:
    """Get ChromaService instance without dependencies (for startup initialization)."""
    global _chroma_service_instance
    if _chroma_service_instance is None:
        client = get_chroma_client()
        _chroma_service_instance = ChromaService(chroma_client=client)
    return _chroma_service_instance


@router.get(
    "/chroma/collections", response_model=List[Dict[str, Any]], tags=["ChromaDB"]
)
def list_collections(service: ChromaService = Depends(get_chroma_service)):
    """
    Lists all collections in ChromaDB.
    """
    try:
        return service.list_collections()
    except Exception as e:
        logger.error(f"Error listing Chroma collections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list collections")


@router.post(
    "/chroma/collections/{collection_name}/query",
    response_model=Dict[str, Any],
    tags=["ChromaDB"],
)
def query_collection(
    collection_name: str,
    query: ChromaQuery,
    service: ChromaService = Depends(get_chroma_service),
):
    """
    Queries a specific collection in ChromaDB.
    """
    try:
        return service.query_collection(
            collection_name=collection_name,
            query_texts=query.query_texts,
            n_results=query.n_results,
            where_filter=query.where_filter,
        )
    except Exception as e:
        logger.error(f"Error querying collection {collection_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to query collection {collection_name}"
        )
