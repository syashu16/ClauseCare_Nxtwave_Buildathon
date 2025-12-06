"""
Authentication Manager for GenLegalAI
Streamlit-native authentication with session-based login
"""

import streamlit as st
import re
from typing import Optional, Callable
from functools import wraps

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_database, User


class AuthManager:
    """Manages user authentication and sessions"""
    
    def __init__(self):
        self.db = get_database()
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize authentication session state"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
        if 'auth_message' not in st.session_state:
            st.session_state.auth_message = None
        if 'auth_message_type' not in st.session_state:
            st.session_state.auth_message_type = None
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _validate_password(self, password: str) -> tuple:
        """
        Validate password strength
        Returns: (is_valid: bool, message: str)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        if not re.search(r'[A-Za-z]', password):
            return False, "Password must contain at least one letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        return True, "Password is valid"
    
    def _validate_username(self, username: str) -> tuple:
        """
        Validate username
        Returns: (is_valid: bool, message: str)
        """
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > 20:
            return False, "Username must be 20 characters or less"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, "Username is valid"
    
    def register(self, username: str, email: str, password: str, confirm_password: str) -> tuple:
        """
        Register a new user
        Returns: (success: bool, message: str)
        """
        # Validate username
        valid, msg = self._validate_username(username)
        if not valid:
            return False, msg
        
        # Validate email
        if not self._validate_email(email):
            return False, "Invalid email format"
        
        # Validate password
        valid, msg = self._validate_password(password)
        if not valid:
            return False, msg
        
        # Check password match
        if password != confirm_password:
            return False, "Passwords do not match"
        
        # Create user
        return self.db.create_user(username, email, password)
    
    def login(self, username: str, password: str) -> tuple:
        """
        Login user
        Returns: (success: bool, message: str)
        """
        if not username or not password:
            return False, "Please enter username and password"
        
        success, user, message = self.db.authenticate_user(username, password)
        
        if success and user:
            st.session_state.authenticated = True
            st.session_state.current_user = user.username
            return True, f"Welcome back, {user.username}!"
        
        return False, message
    
    def logout(self):
        """Logout current user"""
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.auth_message = "Logged out successfully"
        st.session_state.auth_message_type = "success"
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[str]:
        """Get current username"""
        return st.session_state.get('current_user')
    
    def get_user_details(self) -> Optional[User]:
        """Get current user details"""
        username = self.get_current_user()
        if username:
            return self.db.get_user(username)
        return None


def login_form() -> bool:
    """
    Display login form
    Returns: True if login successful
    """
    auth = AuthManager()
    
    st.markdown("### 🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("🔑 Login", use_container_width=True, type="primary")
        
        if submit:
            success, message = auth.login(username, password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
                return False
    
    return auth.is_authenticated()


def register_form() -> bool:
    """
    Display registration form
    Returns: True if registration successful
    """
    auth = AuthManager()
    
    st.markdown("### 📝 Create Account")
    
    with st.form("register_form"):
        username = st.text_input("Username", placeholder="Choose a username (3-20 chars)")
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Min 6 chars, 1 letter, 1 number")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
        
        submit = st.form_submit_button("📝 Register", use_container_width=True, type="primary")
        
        if submit:
            success, message = auth.register(username, email, password, confirm_password)
            if success:
                st.success(f"✅ {message}! Please login.")
                return True
            else:
                st.error(message)
    
    return False


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a function
    Usage: @require_auth
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = AuthManager()
        if not auth.is_authenticated():
            st.warning("🔒 Please login to access this feature")
            
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                login_form()
            
            with tab2:
                if register_form():
                    st.info("Now please login with your credentials")
            
            return None
        
        return func(*args, **kwargs)
    
    return wrapper


def auth_sidebar():
    """Display authentication status in sidebar"""
    auth = AuthManager()
    
    if auth.is_authenticated():
        user = auth.get_current_user()
        st.sidebar.markdown(f"👤 **{user}**")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            auth.logout()
            st.rerun()
    else:
        st.sidebar.markdown("👤 **Guest**")
        st.sidebar.info("Login to save your analysis history")
