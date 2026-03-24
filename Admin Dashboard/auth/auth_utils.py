"""
auth_utils.py — Authentication Utilities Module

Handles user authentication, JWT token generation/verification, and password security.
Used by: Streamlit app for login/register and session management.
"""

import os
import json
import jwt
import bcrypt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

AUTH_DIR = os.path.dirname(os.path.abspath(__file__))
USER_STORE_FILE = os.path.join(AUTH_DIR, "user_store.json")
JWT_SECRET = "agrigraphx-secret-key-2024-internship-project"  # In production, use env var
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# ─────────────────────────────────────────────────────────────────────────────
#  USER STORE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_user_store_exists():
    """Ensure user_store.json exists with proper structure."""
    if not os.path.exists(USER_STORE_FILE):
        initial_data = {"users": {}, "created_at": datetime.now().isoformat()}
        with open(USER_STORE_FILE, "w") as f:
            json.dump(initial_data, f, indent=2)


def _load_users() -> Dict:
    """Load all users from JSON file."""
    _ensure_user_store_exists()
    try:
        with open(USER_STORE_FILE, "r") as f:
            data = json.load(f)
            return data.get("users", {})
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}


def _save_users(users: Dict) -> bool:
    """Save users to JSON file."""
    try:
        _ensure_user_store_exists()
        with open(USER_STORE_FILE, "r") as f:
            data = json.load(f)
        data["users"] = users
        data["modified_at"] = datetime.now().isoformat()
        with open(USER_STORE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  PASSWORD HASHING
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        hashed_password: Hashed password from storage
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  USER REGISTRATION & LOGIN
# ─────────────────────────────────────────────────────────────────────────────

def user_exists(username: str) -> bool:
    """Check if username already exists."""
    users = _load_users()
    return username.lower() in users


def register_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Register a new user.
    
    Args:
        username: Username (must be unique)
        password: Password (minimum 6 characters)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Validation
    username = username.strip().lower()
    
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long."
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    if user_exists(username):
        return False, "Username already exists. Please choose another."
    
    # Hash password and save user
    try:
        users = _load_users()
        hashed_pwd = hash_password(password)
        
        users[username] = {
            "password": hashed_pwd,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        if _save_users(users):
            return True, f"✅ User '{username}' registered successfully!"
        else:
            return False, "Error saving user. Please try again."
    except Exception as e:
        return False, f"Registration error: {str(e)}"


def login_user(username: str, password: str) -> Tuple[bool, str, Optional[str]]:
    """
    Authenticate a user and return JWT token.
    
    Args:
        username: Username
        password: Password
        
    Returns:
        Tuple of (success: bool, message: str, token: str or None)
    """
    username = username.strip().lower()
    users = _load_users()
    
    if username not in users:
        return False, "Username or password incorrect.", None
    
    user_data = users[username]
    
    if not verify_password(password, user_data["password"]):
        return False, "Username or password incorrect.", None
    
    # Generate JWT token
    try:
        token = generate_token(username)
        
        # Update last login
        user_data["last_login"] = datetime.now().isoformat()
        users[username] = user_data
        _save_users(users)
        
        return True, f"✅ Welcome back, {username}!", token
    except Exception as e:
        return False, f"Login error: {str(e)}", None


# ─────────────────────────────────────────────────────────────────────────────
#  JWT TOKEN MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def generate_token(username: str) -> str:
    """
    Generate a JWT token for authenticated user.
    
    Args:
        username: Authenticated username
        
    Returns:
        JWT token string
    """
    payload = {
        "username": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify a JWT token and extract username.
    
    Args:
        token: JWT token string
        
    Returns:
        Tuple of (valid: bool, username: str or None)
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("username")
        return True, username
    except jwt.ExpiredSignatureError:
        return False, None
    except jwt.InvalidTokenError:
        return False, None


# ─────────────────────────────────────────────────────────────────────────────
#  USER MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def get_user_info(username: str) -> Optional[Dict]:
    """Get user information."""
    users = _load_users()
    username = username.lower()
    
    if username in users:
        user_data = users[username].copy()
        user_data.pop("password", None)  # Don't return password
        return user_data
    
    return None


def list_all_users() -> list:
    """List all registered users (excluding passwords)."""
    users = _load_users()
    user_list = []
    
    for username, data in users.items():
        user_info = {
            "username": username,
            "created_at": data.get("created_at"),
            "last_login": data.get("last_login")
        }
        user_list.append(user_info)
    
    return user_list


def delete_user(username: str) -> Tuple[bool, str]:
    """Delete a user (admin function)."""
    users = _load_users()
    username = username.lower()
    
    if username not in users:
        return False, "User not found."
    
    del users[username]
    
    if _save_users(users):
        return True, f"User '{username}' deleted successfully."
    else:
        return False, "Error deleting user."


# ─────────────────────────────────────────────────────────────────────────────
#  UTILITY FUNCTIONS
#  ─────────────────────────────────────────────────────────────────────────────

def is_valid_username(username: str) -> bool:
    """Check if username format is valid."""
    if not username or len(username) < 3:
        return False
    # Only alphanumeric, underscores, hyphens, dots, and @
    return username.replace("_", "").replace("-", "").replace(".", "").replace("@", "").isalnum()


def get_token_expiration_hours() -> int:
    """Get JWT token expiration time in hours."""
    return JWT_EXPIRATION_HOURS
