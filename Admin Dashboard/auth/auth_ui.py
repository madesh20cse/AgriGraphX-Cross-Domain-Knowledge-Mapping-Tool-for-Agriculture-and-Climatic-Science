"""Streamlit Authentication UI Module.

Provides login/register interface and session state management.
Used by: Main app.py to render authentication screens.
"""

import os
import base64
from typing import Optional

import streamlit as st
from .auth_utils import (
	register_user,
	login_user,
	verify_token,
	user_exists,
	is_valid_username,
)


def initialize_session_state() -> None:
	"""Initialize session state variables for authentication."""
	if "user" not in st.session_state:
		st.session_state.user = None
	if "token" not in st.session_state:
		st.session_state.token = None
	if "auth_status" not in st.session_state:
		st.session_state.auth_status = None


def is_authenticated() -> bool:
	"""Check if user is authenticated based on JWT token."""
	if st.session_state.get("token"):
		valid, username = verify_token(st.session_state.token)
		return bool(valid and username == st.session_state.get("user"))
	return False


def _load_background_image_base64() -> Optional[str]:
	"""Return background image as base64 string if available.

	Specifically looks for ``login_bg.avif`` in the assets folder so the
	login screen always uses that image as its background.
	"""

	try:
		base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
		assets_dir = os.path.join(base_dir, "assets")
		if not os.path.isdir(assets_dir):
			return None

		img_path = os.path.join(assets_dir, "login_bg.avif")
		if not os.path.exists(img_path):
			return None

		with open(img_path, "rb") as img_file:
			return base64.b64encode(img_file.read()).decode("utf-8")
	except Exception:
		return None

	return None


def render_auth_page() -> bool:
	"""Render the login/register page.

	Returns:
		bool: True if authentication is successful, False otherwise.
	"""

	initialize_session_state()

	col1, col2, col3 = st.columns([1, 2, 1])

	with col2:
		bg64 = _load_background_image_base64()
		bg_style = ""
		if bg64:
			bg_style = (
				"/* Full-page background image for auth screen */\n"
				"[data-testid=\"stAppViewContainer\"] {\n"
				f"    background-image: url('data:image/avif;base64,{bg64}');\n"
				"    background-size: cover;\n"
				"    background-position: center;\n"
				"    background-repeat: no-repeat;\n"
				"}\n"
			)

		# Heading + styles
		style_block = "<style>\n" + bg_style + """
		@keyframes fadeInScale {
			0% { opacity: 0; transform: translateY(-10px) scale(0.96); }
			100% { opacity: 1; transform: translateY(0) scale(1); }
		}
		@keyframes softGlow {
			0% { box-shadow: 0 0 0 rgba(16,185,129,0.0); }
			100% { box-shadow: 0 18px 45px rgba(16,185,129,0.25); }
		}
		.auth-heading {
			text-align: center;
			font-weight: 800;
			background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
			margin-bottom: 0.5rem;
			animation: fadeInScale 0.7s ease-out;
			line-height: 1.2;
			letter-spacing: -0.5px;
		}
		.auth-subheading {
			text-align: center;
			color: #F9FAFB;
			font-size: 1.1rem;
			font-weight: 500;
			margin-bottom: 1.2rem;
			text-shadow: 0 2px 6px rgba(15,23,42,0.55);
			animation: fadeInScale 0.7s ease-out 0.12s backwards;
		}
		/* Center entire login section */
		.block-container {
			display: flex;
			flex-direction: column;
			align-items: center;
			justify-content: center;
		}

		/* Constrain main content width (login/register area) */
		section.main > div {
			max-width: 420px;
		}

		/* Apply glass effect directly to the container holding the auth forms */
		section.main div[data-testid="stVerticalBlock"] > div {
			background: rgba(0, 0, 0, 0.68);
			backdrop-filter: blur(15px);
			-webkit-backdrop-filter: blur(15px);
			padding: 30px;
			border-radius: 16px;
			box-shadow: 0 8px 32px rgba(0,0,0,0.4);
			color: #E5E7EB;
		}
		section.main div[data-testid="stVerticalBlock"] > div p,
		section.main div[data-testid="stVerticalBlock"] > div li,
		section.main div[data-testid="stVerticalBlock"] > div span {
			color: #E5E7EB;
			text-shadow: 0 1px 3px rgba(0,0,0,0.9);
		}
		.auth-toggle-wrapper {
			background: linear-gradient(135deg, #FFFFFF 0%, #ECFDF5 52%, #EFF6FF 100%);
			border-radius: 999px;
			padding: 0.18rem;
			border: 1px solid rgba(148,163,184,0.5);
			box-shadow: 0 10px 26px rgba(15,118,110,0.18);
			margin-bottom: 0.9rem;
		}
		.stButton > button {
			border-radius: 999px !important;
			font-weight: 600 !important;
			letter-spacing: 0.4px;
			font-size: 0.95rem !important;
			padding: 0.7rem 0.9rem !important;
			transition: all 0.22s ease-in-out !important;
			box-shadow: 0 6px 14px rgba(15,118,110,0.18);
			border: 1px solid rgba(148,163,184,0.6);
			background: linear-gradient(135deg, #FFFFFF 0%, #E5F9F3 100%) !important;
			color: #0F172A !important;
		}
		.stButton > button:hover {
			transform: translateY(-1px) scale(1.01);
			box-shadow: 0 10px 26px rgba(15,118,110,0.32);
			border-color: rgba(16,185,129,0.9);
			background: linear-gradient(135deg, #10B981 0%, #3B82F6 100%) !important;
			color: #FFFFFF !important;
		}
		.stButton > button:active {
			transform: translateY(0px) scale(0.99);
			box-shadow: 0 4px 10px rgba(15,118,110,0.2);
		}
		.stTextInput > div > div,
		.stTextArea > div > div {
			transition: box-shadow 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
		}
		.stTextInput > div > div:focus-within,
		.stTextArea > div > div:focus-within {
			border-color: rgba(16,185,129,0.9) !important;
			box-shadow: 0 0 0 1px rgba(16,185,129,0.7), 0 10px 25px rgba(15,118,110,0.25);
			transform: translateY(-1px);
		}
		/* Glassy inputs and full-width primary buttons */
		section.main div[data-testid="stVerticalBlock"] .stTextInput input,
		section.main div[data-testid="stVerticalBlock"] .stTextArea textarea {
			background: rgba(255,255,255,0.98) !important;
			color: #020617 !important;
			border-radius: 8px !important;
			font-weight: 600;
			box-shadow: 0 4px 12px rgba(15,23,42,0.35);
		}
		section.main div[data-testid="stVerticalBlock"] .stTextInput input::placeholder,
		section.main div[data-testid="stVerticalBlock"] .stTextArea textarea::placeholder {
			color: rgba(15,23,42,0.6);
		}
		button[kind="primary"] {
			width: 100%;
			border-radius: 10px;
		}
		h1, h2, h3 {
			color: white !important;
		}
		label {
			color: #F9FAFB !important;
			font-weight: 600;
			text-shadow: 0 1px 3px rgba(0,0,0,0.9);
		}
		</style>
		"""

		st.markdown(style_block, unsafe_allow_html=True)
		st.markdown("---")
		st.markdown(
			"""
		<h2 class="auth-heading">🌱 AgriGraphX Cross Domain Knowledge Mapping Tool</h2>
		<div class="auth-subheading">User Authentication</div>
		""",
			unsafe_allow_html=True,
		)

		# Toggle buttons for Login / Register
		if "auth_mode" not in st.session_state:
			st.session_state.auth_mode = "login"
		st.markdown("<div class='auth-toggle-wrapper'>", unsafe_allow_html=True)
		toggle_col1, toggle_col2 = st.columns(2)
		with toggle_col1:
			if st.button("🔐 Login", use_container_width=True):
				st.session_state.auth_mode = "login"
		with toggle_col2:
			if st.button("📝 Register", use_container_width=True):
				st.session_state.auth_mode = "register"
		st.markdown("</div>", unsafe_allow_html=True)

		# ─────────────────────────────────────────────────────────────────────
		#  LOGIN VIEW
		# ─────────────────────────────────────────────────────────────────────
		if st.session_state.auth_mode == "login":
			st.markdown("### Sign In to Your Account")

			with st.form("login_form", clear_on_submit=False):
				username = st.text_input(
					"Username",
					key="login_username",
					help="Enter your username",
				)

				password = st.text_input(
					"Password",
					type="password",
					key="login_password",
					help="Enter your password",
				)

				col_btn1, col_btn2 = st.columns(2)

				with col_btn1:
					login_btn = st.form_submit_button(
						"🔐 Sign In",
						use_container_width=True,
						type="primary",
					)

				with col_btn2:
					st.form_submit_button(
						"Clear",
						use_container_width=True,
						type="secondary",
					)

				if login_btn:
					if not username or not password:
						st.error("❌ Please enter username and password.")
					else:
						success, message, token = login_user(username, password)

						if success:
							# Normalize username for session state to match backend storage
							st.session_state.user = username.strip().lower()
							st.session_state.token = token
							st.session_state.auth_status = "success"
							st.success(message)
							st.balloons()
							st.rerun()
						else:
							st.error(f"❌ {message}")
							st.session_state.auth_status = "failed"

			st.markdown("")
			st.info(
				"💡 New user? Click **Register** above to create an account."
			)

		# ─────────────────────────────────────────────────────────────────────
		#  REGISTER VIEW
		# ─────────────────────────────────────────────────────────────────────
		else:
			st.markdown("### Create a New Account")

			with st.form("register_form", clear_on_submit=False):
				new_username = st.text_input(
					"Choose Username",
					key="reg_username",
					help="Username must be 3+ characters (letters, numbers, dash, underscore)",
				)

				# Real-time username validation
				if new_username:
					if user_exists(new_username):
						st.error(f"❌ Username '{new_username}' already taken.")
					elif not is_valid_username(new_username):
						st.error("❌ Username contains invalid characters.")
					elif len(new_username) < 3:
						st.error("❌ Username must be at least 3 characters.")
					else:
						st.success(
							f"✅ Username '{new_username}' is available!"
						)

				new_password = st.text_input(
					"Choose Password",
					type="password",
					key="reg_password",
					help="Password must be at least 6 characters",
				)

				confirm_password = st.text_input(
					"Confirm Password",
					type="password",
					key="reg_confirm",
					help="Re-enter your password",
				)

				col_btn1, col_btn2 = st.columns(2)

				with col_btn1:
					register_btn = st.form_submit_button(
						"✅ Create Account",
						use_container_width=True,
						type="primary",
					)

				with col_btn2:
					st.form_submit_button(
						"Clear",
						use_container_width=True,
						type="secondary",
					)

				if register_btn:
					# Validation
					if not new_username or not new_password:
						st.error("❌ Please fill in all fields.")
					elif not is_valid_username(new_username):
						st.error(
							"❌ Username contains invalid characters or is too short."
						)
					elif new_password != confirm_password:
						st.error("❌ Passwords do not match.")
					else:
						success, message = register_user(
							new_username, new_password
						)

						if success:
							st.success(message)
							st.info(
								"Great! Your account is ready. Click **Login** above to sign in."
							)
						else:
							st.error(f"❌ {message}")

			st.markdown("")
			st.info(
				"💡 Already have an account? Click **Login** above."
			)

	# Return whether user is now authenticated
	return is_authenticated()


def render_user_info() -> None:
	"""Render basic information about the current user.

	This is a lightweight helper so imports from auth.__init__ and
	app.py succeed even if the UI chooses not to use it directly.
	"""

	user = st.session_state.get("user")
	if user:
		st.markdown(f"**Logged in as:** `{user}`")
	else:
		st.markdown("**Not logged in**")


def render_logout_button(label: str = "🚪 Logout") -> None:
	"""Render a simple logout button.

	Provided for backwards compatibility with earlier layouts that
	called this helper directly.
	"""

	if st.button(label):
		st.session_state.user = None
		st.session_state.token = None
		st.session_state.auth_status = None
		st.success("✅ Logged out successfully!")
		st.rerun()


def require_auth() -> bool:
	"""Guard helper that can be used by pages to enforce auth.

	Returns True when the user is authenticated; otherwise renders the
	auth page and returns False.
	"""

	if is_authenticated():
		return True

	render_auth_page()
	return False

