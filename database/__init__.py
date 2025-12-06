"""
Database Module for GenLegalAI
Provides cloud-compatible data persistence using JSON files for Streamlit Cloud deployment.
"""

from .db_manager import DatabaseManager, User, AnalysisHistory

__all__ = ['DatabaseManager', 'User', 'AnalysisHistory']
