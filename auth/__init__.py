"""
Authentication Module for GenLegalAI
Provides Streamlit-native authentication with session management
"""

from .auth_manager import AuthManager, login_form, register_form, require_auth

__all__ = ['AuthManager', 'login_form', 'register_form', 'require_auth']
