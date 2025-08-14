# src/api/routes/cms.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
import logging
from typing import List, Optional
import os
import json
from datetime import datetime
import shutil
from src.models.intent import Intent, KnowledgeBase
from src.utils.data_utils import load_json_file, save_json_file, backup_knowledge_base

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cms", tags=["cms"])

# Base paths for data and audio files
DATA_BASE_PATH = "data/sources"
AUDIO_BASE_PATH = "data/audio"
BACKUP_BASE_PATH = "data/sources"


@router.get("/intents/{language}")
async def get_intents(language: str):
    """
    Get all intents for a specific language
    """
    try:
        file_path = os.path.join(DATA_BASE_PATH, language, f"dialog-{language}.json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        data = load_json_file(file_path)
        return data
    except Exception as e:
        logger.error(f"Error retrieving intents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/intents/{language}")
async def update_intents(language: str, intents: List[Intent]):
    """
    Update all intents for a specific language
    """
    try:
        file_path = os.path.join(DATA_BASE_PATH, language, f"dialog-{language}.json")
        backup_path = os.path.join(BACKUP_BASE_PATH, language, "history")
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Create backup before updating
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file_name = f"dialog-{language}-{timestamp}.json"
        backup_file_path = os.path.join(backup_path, backup_file_name)
        
        # Ensure backup directory exists
        os.makedirs(backup_path, exist_ok=True)
        
        # Copy current file to backup
        shutil.copy2(file_path, backup_file_path)
        
        # Load existing data to preserve metadata
        existing_data = load_json_file(file_path)
        
        # Update the intents
        existing_data["intents"] = [intent.model_dump() for intent in intents]
        existing_data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        # Save updated data
        save_json_file(existing_data, file_path)
        
        return {"message": "Intents updated successfully", "backup_created": backup_file_name}
    except Exception as e:
        logger.error(f"Error updating intents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intents/{language}/{intent_id}")
async def get_intent(language: str, intent_id: str):
    """
    Get a specific intent by ID for a specific language
    """
    try:
        file_path = os.path.join(DATA_BASE_PATH, language, f"dialog-{language}.json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        data = load_json_file(file_path)
        for intent in data.get("intents", []):
            if intent.get("id") == intent_id:
                return intent
        
        raise HTTPException(status_code=404, detail="Intent not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intents/{language}")
async def create_intent(language: str, intent: Intent):
    """
    Create a new intent for a specific language
    """
    try:
        file_path = os.path.join(DATA_BASE_PATH, language, f"dialog-{language}.json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Load existing data
        data = load_json_file(file_path)
        
        # Check if intent ID already exists
        for existing_intent in data.get("intents", []):
            if existing_intent.get("id") == intent.id:
                raise HTTPException(status_code=400, detail="Intent ID already exists")
        
        # Add new intent
        data["intents"].append(intent.model_dump())
        data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        # Save updated data
        save_json_file(data, file_path)
        
        return {"message": "Intent created successfully", "intent_id": intent.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/intents/{language}/{intent_id}")
async def update_intent(language: str, intent_id: str, intent: Intent):
    """
    Update a specific intent by ID for a specific language
    """
    try:
        file_path = os.path.join(DATA_BASE_PATH, language, f"dialog-{language}.json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Load existing data
        data = load_json_file(file_path)
        
        # Find and update the intent
        intent_found = False
        for i, existing_intent in enumerate(data.get("intents", [])):
            if existing_intent.get("id") == intent_id:
                data["intents"][i] = intent.model_dump()
                intent_found = True
                break
        
        if not intent_found:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        # Update metadata
        data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        # Save updated data
        save_json_file(data, file_path)
        
        return {"message": "Intent updated successfully", "intent_id": intent_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/intents/{language}/{intent_id}")
async def delete_intent(language: str, intent_id: str):
    """
    Delete a specific intent by ID for a specific language
    """
    try:
        file_path = os.path.join(DATA_BASE_PATH, language, f"dialog-{language}.json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        # Load existing data
        data = load_json_file(file_path)
        
        # Find and remove the intent
        intent_found = False
        for i, existing_intent in enumerate(data.get("intents", [])):
            if existing_intent.get("id") == intent_id:
                data["intents"].pop(i)
                intent_found = True
                break
        
        if not intent_found:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        # Update metadata
        data["metadata"]["updated_at"] = datetime.now().isoformat()
        
        # Save updated data
        save_json_file(data, file_path)
        
        return {"message": "Intent deleted successfully", "intent_id": intent_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio/{language}/{response_id}")
async def upload_audio(
    language: str, 
    response_id: str, 
    file: UploadFile = File(...)
):
    """
    Upload an audio file for a specific response
    """
    try:
        # Validate file type
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Create directory if it doesn't exist
        audio_dir = os.path.join(AUDIO_BASE_PATH, language)
        os.makedirs(audio_dir, exist_ok=True)
        
        # Save file
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "mp3"
        file_path = os.path.join(audio_dir, f"{response_id}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"message": "Audio file uploaded successfully", "file_path": file_path}
    except Exception as e:
        logger.error(f"Error uploading audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio/{language}/{response_id}")
async def get_audio(language: str, response_id: str):
    """
    Get an audio file for a specific response
    """
    try:
        # Try different file extensions
        extensions = ["mp3", "wav", "ogg", "m4a"]
        file_path = None
        
        for ext in extensions:
            path = os.path.join(AUDIO_BASE_PATH, language, f"{response_id}.{ext}")
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/audio/{language}/{response_id}")
async def delete_audio(language: str, response_id: str):
    """
    Delete an audio file for a specific response
    """
    try:
        # Try different file extensions
        extensions = ["mp3", "wav", "ogg", "m4a"]
        file_path = None
        
        for ext in extensions:
            path = os.path.join(AUDIO_BASE_PATH, language, f"{response_id}.{ext}")
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        os.remove(file_path)
        return {"message": "Audio file deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups/{language}")
async def list_backups(language: str):
    """
    List all backups for a specific language
    """
    try:
        backup_path = os.path.join(BACKUP_BASE_PATH, language, "history")
        if not os.path.exists(backup_path):
            return []
        
        backups = []
        for file in os.listdir(backup_path):
            if file.startswith(f"dialog-{language}-") and file.endswith(".json"):
                file_path = os.path.join(backup_path, file)
                stat = os.stat(file_path)
                backups.append({
                    "filename": file,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size
                })
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backups/{language}/{backup_filename}/restore")
async def restore_backup(language: str, backup_filename: str):
    """
    Restore a specific backup for a language
    """
    try:
        backup_path = os.path.join(BACKUP_BASE_PATH, language, "history", backup_filename)
        target_path = os.path.join(DATA_BASE_PATH, language, f"dialog-{language}.json")
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Create a backup of current file before restoring
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        current_backup = os.path.join(BACKUP_BASE_PATH, language, "history", f"dialog-{language}-{timestamp}-before-restore.json")
        os.makedirs(os.path.dirname(current_backup), exist_ok=True)
        shutil.copy2(target_path, current_backup)
        
        # Restore the backup
        shutil.copy2(backup_path, target_path)
        
        return {"message": "Backup restored successfully", "backup_used": backup_filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))