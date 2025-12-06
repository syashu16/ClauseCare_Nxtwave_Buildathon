"""
Database Manager for GenLegalAI
Uses JSON files for simple persistence - works on Streamlit Cloud
For production, can be swapped with Supabase/Firebase
"""

import json
import os
import hashlib
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class User:
    """User data model"""
    username: str
    email: str
    password_hash: str
    created_at: str
    last_login: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(**data)


@dataclass
class AnalysisHistory:
    """Analysis history entry"""
    id: str
    username: str
    document_name: str
    analysis_type: str  # 'risk', 'negotiate', 'translate', 'simplify', 'chat'
    summary: str
    result_data: Dict[str, Any]
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisHistory':
        return cls(**data)


class DatabaseManager:
    """
    Simple JSON-based database manager for Streamlit Cloud deployment.
    Stores data in JSON files which persist across sessions.
    
    For production scaling, replace with Supabase:
    - pip install supabase
    - Use Supabase client instead of file operations
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize database manager"""
        self.data_dir = Path(data_dir)
        self.users_file = self.data_dir / "users.json"
        self.history_file = self.data_dir / "history.json"
        
        # Create data directory if not exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize files if not exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        if not self.users_file.exists():
            self._write_json(self.users_file, {"users": {}})
        
        if not self.history_file.exists():
            self._write_json(self.history_file, {"history": []})
    
    def _read_json(self, filepath: Path) -> Dict[str, Any]:
        """Read JSON file safely"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _write_json(self, filepath: Path, data: Dict[str, Any]):
        """Write JSON file safely"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # ==================
    # Password Hashing
    # ==================
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Hash password with salt
        password_hash = hashlib.sha256(
            (password + salt).encode()
        ).hexdigest()
        
        # Return combined hash (salt:hash)
        return f"{salt}:{password_hash}", salt
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, hash_value = stored_hash.split(':')
            new_hash, _ = self._hash_password(password, salt)
            return new_hash == stored_hash
        except ValueError:
            return False
    
    # ==================
    # User Management
    # ==================
    
    def create_user(self, username: str, email: str, password: str) -> tuple:
        """
        Create a new user
        Returns: (success: bool, message: str)
        """
        data = self._read_json(self.users_file)
        
        # Check if username exists
        if username.lower() in [u.lower() for u in data.get("users", {}).keys()]:
            return False, "Username already exists"
        
        # Check if email exists
        for user_data in data.get("users", {}).values():
            if user_data.get("email", "").lower() == email.lower():
                return False, "Email already registered"
        
        # Create password hash
        password_hash, _ = self._hash_password(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            created_at=datetime.now().isoformat()
        )
        
        # Save user
        data["users"][username] = user.to_dict()
        self._write_json(self.users_file, data)
        
        return True, "User created successfully"
    
    def authenticate_user(self, username: str, password: str) -> tuple:
        """
        Authenticate user
        Returns: (success: bool, user: Optional[User], message: str)
        """
        data = self._read_json(self.users_file)
        users = data.get("users", {})
        
        # Find user (case-insensitive)
        user_data = None
        actual_username = None
        for uname, udata in users.items():
            if uname.lower() == username.lower():
                user_data = udata
                actual_username = uname
                break
        
        if not user_data:
            return False, None, "User not found"
        
        # Verify password
        if not self._verify_password(password, user_data.get("password_hash", "")):
            return False, None, "Invalid password"
        
        # Update last login
        user_data["last_login"] = datetime.now().isoformat()
        data["users"][actual_username] = user_data
        self._write_json(self.users_file, data)
        
        return True, User.from_dict(user_data), "Login successful"
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        data = self._read_json(self.users_file)
        user_data = data.get("users", {}).get(username)
        
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def update_user_password(self, username: str, new_password: str) -> bool:
        """Update user password"""
        data = self._read_json(self.users_file)
        
        if username not in data.get("users", {}):
            return False
        
        password_hash, _ = self._hash_password(new_password)
        data["users"][username]["password_hash"] = password_hash
        self._write_json(self.users_file, data)
        
        return True
    
    # ==================
    # History Management
    # ==================
    
    def save_analysis(
        self,
        username: str,
        document_name: str,
        analysis_type: str,
        summary: str,
        result_data: Dict[str, Any]
    ) -> str:
        """
        Save analysis to history
        Returns: analysis_id
        """
        data = self._read_json(self.history_file)
        
        # Generate unique ID
        analysis_id = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        # Create history entry
        entry = AnalysisHistory(
            id=analysis_id,
            username=username,
            document_name=document_name,
            analysis_type=analysis_type,
            summary=summary,
            result_data=result_data,
            created_at=datetime.now().isoformat()
        )
        
        # Add to history
        data.setdefault("history", []).append(entry.to_dict())
        
        # Keep only last 100 entries per user to avoid file bloat
        user_entries = [h for h in data["history"] if h["username"] == username]
        if len(user_entries) > 100:
            # Remove oldest entries
            oldest_ids = [h["id"] for h in sorted(user_entries, key=lambda x: x["created_at"])[:len(user_entries)-100]]
            data["history"] = [h for h in data["history"] if h["id"] not in oldest_ids]
        
        self._write_json(self.history_file, data)
        
        return analysis_id
    
    def get_user_history(
        self,
        username: str,
        analysis_type: Optional[str] = None,
        limit: int = 20
    ) -> List[AnalysisHistory]:
        """Get user's analysis history"""
        data = self._read_json(self.history_file)
        
        # Filter by username
        history = [
            h for h in data.get("history", [])
            if h["username"] == username
        ]
        
        # Filter by type if specified
        if analysis_type:
            history = [h for h in history if h["analysis_type"] == analysis_type]
        
        # Sort by date (newest first) and limit
        history = sorted(history, key=lambda x: x["created_at"], reverse=True)[:limit]
        
        return [AnalysisHistory.from_dict(h) for h in history]
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[AnalysisHistory]:
        """Get specific analysis by ID"""
        data = self._read_json(self.history_file)
        
        for entry in data.get("history", []):
            if entry["id"] == analysis_id:
                return AnalysisHistory.from_dict(entry)
        
        return None
    
    def delete_analysis(self, analysis_id: str, username: str) -> bool:
        """Delete analysis (only by owner)"""
        data = self._read_json(self.history_file)
        
        original_len = len(data.get("history", []))
        data["history"] = [
            h for h in data.get("history", [])
            if not (h["id"] == analysis_id and h["username"] == username)
        ]
        
        if len(data["history"]) < original_len:
            self._write_json(self.history_file, data)
            return True
        
        return False
    
    def clear_user_history(self, username: str) -> int:
        """Clear all history for a user. Returns count of deleted entries."""
        data = self._read_json(self.history_file)
        
        original_len = len([h for h in data.get("history", []) if h["username"] == username])
        data["history"] = [h for h in data.get("history", []) if h["username"] != username]
        
        self._write_json(self.history_file, data)
        
        return original_len
    
    # ==================
    # Statistics
    # ==================
    
    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Get user statistics"""
        history = self.get_user_history(username, limit=1000)
        
        stats = {
            "total_analyses": len(history),
            "by_type": {},
            "documents_analyzed": len(set(h.document_name for h in history)),
            "last_analysis": history[0].created_at if history else None
        }
        
        # Count by type
        for h in history:
            stats["by_type"][h.analysis_type] = stats["by_type"].get(h.analysis_type, 0) + 1
        
        return stats


# Singleton instance for easy access
_db_instance: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
