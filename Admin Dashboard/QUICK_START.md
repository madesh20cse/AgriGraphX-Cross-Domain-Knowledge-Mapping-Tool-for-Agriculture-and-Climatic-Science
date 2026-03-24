# Quick Start Guide - AgriGraphX Module 1

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
cd "Admin Dashboard"
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run app.py
```

### 3. Register & Login
- Open browser → http://localhost:8501
- Click **Register** tab
- Create account with username & password (min 6 chars)
- Switch to **Login** tab and sign in

### 4. Select Dataset
- Click **📂 Dataset Selection** in sidebar
- Choose data source:
  - **📂 Upload File** — Upload CSV/TXT/JSON
  - **📖 Wikipedia** — Fetch articles
  - **📰 News** — Browse curated news
  - **📚 Sample Datasets** — Use pre-loaded data

### 5. Process & Graph
- Dataset content stored automatically
- Navigate to other modules for processing
- Knowledge graph builds from selected data

---

## 🔑 Demo Account (After First Run)

Create a demo account during first run, then use:

```python
# To create demo account programmatically:
from auth import register_user
register_user("demo", "demo123")
```

---

## 📊 What's New

### Module 1 Adds:
✅ JWT-based user authentication
✅ Secure password hashing (bcrypt)
✅ Multi-source dataset selection
✅ File upload processing
✅ Wikipedia integration
✅ News data connector
✅ Session management

### File Structure Added:
```
auth/
├── auth_utils.py
├── auth_ui.py
└── user_store.json

connectors/
├── file_uploader.py
├── wikipedia_connector.py
├── news_connector.py
└── __init__.py

dataset_selection_ui.py
```

---

## 🛡️ Security Features

- Passwords hashed with bcrypt (10 rounds)
- JWT tokens with 24-hour expiration
- Session verification on each request
- File validation (format, size, encoding)

---

## 📚 Helpful Commands

```bash
# Test authentication module
python -c "from auth import register_user; \
register_user('testuser', 'password123')"

# Check installed packages
pip list | grep -E "PyJWT|bcrypt|wikipedia"

# Clear user database (start fresh)
rm auth/user_store.json

# Start with debug logging
streamlit run app.py --logger.level=debug
```

---

## ✨ Features by Data Source

### File Upload
- Formats: CSV, TXT, JSON
- Max size: 50MB
- Auto-converted to text

### Wikipedia
- Live Wikipedia search
- Full article fetch
- Metadata extraction

### News (Mock)
- Categories: Agriculture, Climate, AI Tech
- Searchable articles
- Expandable design

### Sample Datasets
- Pre-loaded by domain
- 5-10 documents each
- Instant selection

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Login fails | Verify username/password (case-insensitive) |
| File won't upload | Check format (CSV/TXT/JSON) and size |
| Wikipedia returns nothing | Try different keywords |
| Token expired | Log out and log back in |

---

## 🚀 Next Steps

1. ✅ Create account and log in
2. ✅ Select a dataset
3. ✅ Explore other modules with your data
4. ✅ Build knowledge graphs
5. ✅ Refine and validate results

---

**Ready to go?** Run `streamlit run app.py` and create your first account! 🌱
