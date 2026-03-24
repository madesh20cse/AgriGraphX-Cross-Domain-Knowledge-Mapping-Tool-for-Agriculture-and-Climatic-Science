"""User profile management for AgriGraphX.

JSON-backed storage for per-user preferences, saved graphs,
and dataset history, keyed by the authenticated username/email.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


AUTH_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(AUTH_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


def _ensure_users_file_exists() -> None:
    """Make sure the users.json file exists and is valid JSON.

    If the file is missing or corrupted, it is recreated with a
    minimal valid structure so that subsequent reads/writes work.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    default_payload = {
        "users": {},
        "created_at": datetime.now().isoformat(),
    }

    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_payload, f, indent=2)
        return

    # File exists – verify that it's valid JSON; if not, reset it.
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            json.load(f)
    except Exception:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_payload, f, indent=2)


def load_users() -> Dict[str, Dict[str, Any]]:
    """Load all user profiles from JSON file.

    Returns:
        Dict mapping email/username to profile dict.
    """
    _ensure_users_file_exists()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        users = data.get("users", {})
        # Ensure structure is always dict
        if isinstance(users, dict):
            return users
        return {}
    except Exception:
        return {}


def save_users(users: Dict[str, Dict[str, Any]]) -> bool:
    """Persist all user profiles to JSON file.

    Args:
        users: Dict mapping email/username to profile dict.
    """
    try:
        _ensure_users_file_exists()
        meta: Dict[str, Any]
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
            # Preserve any top-level metadata if present
            meta = {k: v for k, v in existing.items() if k != "users"}
        except Exception:
            # If the file is unreadable for any reason, fall back
            # to a fresh metadata wrapper.
            meta = {"created_at": datetime.now().isoformat()}

        meta["users"] = users
        meta["modified_at"] = datetime.now().isoformat()
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        return True
    except Exception:
        return False


def _default_profile(email: str) -> Dict[str, Any]:
    """Create a default profile structure for a new user."""
    return {
        "email": email,
        # Password here is not used for authentication; the
        # canonical hash lives in auth/user_store.json.
        "password": "",
        "preferences": {
            "theme": "light",
            "default_domain": "Agriculture",
        },
        "saved_graphs": [],
        "dataset_history": [],
    }


def get_user(email: str) -> Optional[Dict[str, Any]]:
    """Get a user profile by email/username.

    If no profile exists yet, a default profile is created,
    persisted, and returned.
    """
    if not email:
        return None

    email_key = email.strip().lower()
    users = load_users()
    if email_key not in users:
        users[email_key] = _default_profile(email_key)
        save_users(users)
    return users.get(email_key)


def update_user(email: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update (merge) fields for a given user profile.

    Args:
        email: User identifier (username/email)
        data:  Partial profile data to merge. "preferences" is
               merged shallowly; other keys overwrite existing
               values.

    Returns:
        The updated profile dict, or None if email is invalid.
    """
    if not email:
        return None

    email_key = email.strip().lower()
    users = load_users()
    profile = users.get(email_key) or _default_profile(email_key)

    for key, value in data.items():
        if key == "preferences" and isinstance(value, dict):
            existing_prefs = profile.get("preferences", {})
            if not isinstance(existing_prefs, dict):
                existing_prefs = {}
            merged = {**existing_prefs, **value}
            profile["preferences"] = merged
        else:
            profile[key] = value

    users[email_key] = profile
    save_users(users)
    return profile
