# src/utils/data_utils.py
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file with error handling"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {file_path}: {e}")


def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2):
    """Save data to JSON file with proper formatting"""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)


def validate_knowledge_base_structure(data: Dict[str, Any]) -> List[str]:
    """Validate knowledge base structure and return list of issues"""
    issues = []

    # Check required top-level keys
    if "intents" not in data:
        issues.append("Missing 'intents' key")
        return issues

    if not isinstance(data["intents"], list):
        issues.append("'intents' must be a list")
        return issues

    # Check each intent
    for i, intent in enumerate(data["intents"]):
        prefix = f"Intent {i}: "

        # Required fields
        required_fields = ["id", "patterns", "responses", "metadata"]
        for field in required_fields:
            if field not in intent:
                issues.append(f"{prefix}Missing required field '{field}'")

        # Check patterns
        if "patterns" in intent:
            if not isinstance(intent["patterns"], list) or not intent["patterns"]:
                issues.append(f"{prefix}Patterns must be a non-empty list")

        # Check responses
        if "responses" in intent:
            if not isinstance(intent["responses"], list) or not intent["responses"]:
                issues.append(f"{prefix}Responses must be a non-empty list")

        # Check metadata
        if "metadata" in intent:
            metadata = intent["metadata"]
            if "category" not in metadata:
                issues.append(f"{prefix}Missing category in metadata")

    return issues


def backup_knowledge_base(source_file: str, backup_dir: str = "backups") -> str:
    """Create a backup of the knowledge base"""
    if not os.path.exists(source_file):
        raise FileNotFoundError(f"Source file not found: {source_file}")

    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"knowledge_base_backup_{timestamp}.json"
    backup_path = os.path.join(backup_dir, backup_filename)

    # Copy file
    import shutil

    shutil.copy2(source_file, backup_path)

    return backup_path
