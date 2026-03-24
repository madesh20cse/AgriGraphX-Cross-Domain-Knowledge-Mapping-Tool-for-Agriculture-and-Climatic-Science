"""
auth — Authentication and Authorization Module

Submodules:
  - auth_utils.py: JWT, password hashing, user management
  - auth_ui.py: Streamlit login/register UI
"""

from .auth_utils import (
    register_user,
    login_user,
    verify_token,
    generate_token,
    user_exists,
    hash_password,
    verify_password,
    get_user_info,
    list_all_users,
    delete_user,
)

from .auth_ui import (
    initialize_session_state,
    is_authenticated,
    render_auth_page,
    render_user_info,
    render_logout_button,
    require_auth,
)

__all__ = [
    "register_user",
    "login_user",
    "verify_token",
    "generate_token",
    "user_exists",
    "hash_password",
    "verify_password",
    "get_user_info",
    "list_all_users",
    "delete_user",
    "initialize_session_state",
    "is_authenticated",
    "render_auth_page",
    "render_user_info",
    "render_logout_button",
    "require_auth",
]
